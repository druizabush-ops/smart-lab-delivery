"""Простой wiring зависимостей без DI-фреймворков."""

from src.application.services import (
    DeduplicationPolicy,
    DeliveryCardReadService,
    DeliveryPolicy,
    FallbackPolicy,
    OperatorActionPolicy,
    RetryLimits,
    RetryPolicy,
)
from src.application.services.delivery_orchestrator import DeliveryOrchestrator
from src.application.use_cases import (
    CreateDeliveryCardUseCase,
    HandleDeliveryFailureUseCase,
    MoveToManualReviewCommandUseCase,
    OverrideChannelCommandUseCase,
    ProcessDeliveryUseCase,
    RequeueDeliveryCardCommandUseCase,
    RegisterDeliveryResultUseCase,
    RetryDeliveryCardCommandUseCase,
    RetryDeliveryUseCase,
)
from src.config.integration_settings import EmailSettings, MaxSettings, RenovatioSettings
from src.config.runtime_settings import RuntimeSettings
from src.config.security_settings import SecuritySettings
from src.domain.entities import Patient
from src.infrastructure.logging import configure_logging
from src.infrastructure.queue import InMemoryDeliveryQueue
from src.infrastructure.repositories import InMemoryDeliveryCardRepository
from src.infrastructure.runtime import DeliveryProcessManager, DeliveryRuntime, DeliveryRuntimeSelector
from src.infrastructure.session import InMemoryPatientSessionRepository
from src.integration.delivery import EmailDeliveryProvider, MaxDeliveryProvider
from src.integration.logging import LoggerAdapter, OperatorActionLoggerAdapter
from src.integration.renovatio import RenovatioClient
from src.application.use_cases.patient_auth import (
    ConfirmPatientAuthCodeUseCase,
    GetCurrentPatientUseCase,
    PatientLoginUseCase,
    PatientPhoneLoginUseCase,
    RefreshPatientSessionUseCase,
)


class AppContainer:
    """Собирает интеграции, application use cases и runtime-контур исполнения."""

    def __init__(self) -> None:
        configure_logging()
        self.runtime_settings = RuntimeSettings.from_env()
        self.security_settings = SecuritySettings.from_env()

        self.renovatio_settings = RenovatioSettings.from_env()
        self.max_settings = MaxSettings.from_env()
        self.email_settings = EmailSettings.from_env()
        self.renovatio_settings.validate_for_mode(self.runtime_settings.integration_mode, self.runtime_settings.environment)
        self.max_settings.validate_for_mode(self.runtime_settings.integration_mode, self.runtime_settings.environment)
        self.email_settings.validate_for_mode(self.runtime_settings.integration_mode, self.runtime_settings.environment)

        integration_mode = self.runtime_settings.integration_mode

        self.renovatio_client = RenovatioClient(
            mode=integration_mode,
            settings=self.renovatio_settings,
        )
        self.max_delivery_provider = MaxDeliveryProvider(
            mode=integration_mode,
            settings=self.max_settings,
        )
        self.email_delivery_provider = EmailDeliveryProvider(
            mode=integration_mode,
            settings=self.email_settings,
        )
        self.notification_logger = LoggerAdapter()
        self.delivery_card_repository = self._build_delivery_card_repository()
        self.operator_action_logger = OperatorActionLoggerAdapter(audit_repository=self._build_operator_audit_repository())

        self.retry_policy = RetryPolicy(
            RetryLimits(
                max_total_attempts=4,
                max_max_attempts=2,
                max_email_attempts=2,
            )
        )
        self.fallback_policy = FallbackPolicy()
        self.deduplication_policy = DeduplicationPolicy()
        self.delivery_policy = DeliveryPolicy(
            retry_policy=self.retry_policy,
            fallback_policy=self.fallback_policy,
            deduplication_policy=self.deduplication_policy,
        )
        self.operator_action_policy = OperatorActionPolicy()

        self.create_delivery_card_use_case = CreateDeliveryCardUseCase()
        self.register_delivery_result_use_case = RegisterDeliveryResultUseCase()
        self.handle_delivery_failure_use_case = HandleDeliveryFailureUseCase(
            delivery_policy=self.delivery_policy,
        )
        self.process_delivery_use_case = ProcessDeliveryUseCase(
            max_delivery_provider=self.max_delivery_provider,
            email_delivery_provider=self.email_delivery_provider,
            delivery_policy=self.delivery_policy,
            register_result_use_case=self.register_delivery_result_use_case,
            failure_use_case=self.handle_delivery_failure_use_case,
            notification_logger=self.notification_logger,
        )
        self.retry_delivery_use_case = RetryDeliveryUseCase(
            max_delivery_provider=self.max_delivery_provider,
            email_delivery_provider=self.email_delivery_provider,
            delivery_policy=self.delivery_policy,
            register_result_use_case=self.register_delivery_result_use_case,
            failure_use_case=self.handle_delivery_failure_use_case,
            notification_logger=self.notification_logger,
        )
        self.retry_delivery_card_command_use_case = RetryDeliveryCardCommandUseCase(
            repository=self.delivery_card_repository,
            policy=self.operator_action_policy,
            retry_use_case=self.retry_delivery_use_case,
            action_logger=self.operator_action_logger,
        )
        self.move_to_manual_review_command_use_case = MoveToManualReviewCommandUseCase(
            repository=self.delivery_card_repository,
            policy=self.operator_action_policy,
            action_logger=self.operator_action_logger,
        )
        self.requeue_delivery_card_command_use_case = RequeueDeliveryCardCommandUseCase(
            repository=self.delivery_card_repository,
            policy=self.operator_action_policy,
            action_logger=self.operator_action_logger,
        )
        self.override_channel_command_use_case = OverrideChannelCommandUseCase(
            repository=self.delivery_card_repository,
            policy=self.operator_action_policy,
            action_logger=self.operator_action_logger,
        )

        self.delivery_orchestrator = DeliveryOrchestrator(
            lab_result_provider=self.renovatio_client,
            create_delivery_card_use_case=self.create_delivery_card_use_case,
            process_delivery_use_case=self.process_delivery_use_case,
            retry_delivery_use_case=self.retry_delivery_use_case,
        )

        self.delivery_queue = InMemoryDeliveryQueue()
        self.delivery_runtime = DeliveryRuntime(
            orchestrator=self.delivery_orchestrator,
            repository=self.delivery_card_repository,
            queue=self.delivery_queue,
        )

        self.delivery_runtime_selector = DeliveryRuntimeSelector(
            repository=self.delivery_card_repository,
        )
        self.delivery_process_manager = DeliveryProcessManager(
            runtime=self.delivery_runtime,
            selector=self.delivery_runtime_selector,
        )

        self.delivery_card_read_service = DeliveryCardReadService(
            repository=self.delivery_card_repository,
        )
        self.patient_session_repository = InMemoryPatientSessionRepository()
        self.patient_login_use_case = PatientLoginUseCase(
            client=self.renovatio_client,
            session_repository=self.patient_session_repository,
            session_ttl_minutes=self.security_settings.patient_session_ttl_minutes,
            key_lifetime_minutes=self.renovatio_settings.patient_key_lifetime_minutes,
        )
        self.patient_phone_login_use_case = PatientPhoneLoginUseCase(client=self.renovatio_client)
        self.confirm_patient_auth_code_use_case = ConfirmPatientAuthCodeUseCase(
            client=self.renovatio_client,
            session_repository=self.patient_session_repository,
            session_ttl_minutes=self.security_settings.patient_session_ttl_minutes,
        )
        self.refresh_patient_session_use_case = RefreshPatientSessionUseCase(
            client=self.renovatio_client,
            session_repository=self.patient_session_repository,
            session_ttl_minutes=self.security_settings.patient_session_ttl_minutes,
            key_lifetime_minutes=self.renovatio_settings.patient_key_lifetime_minutes,
        )
        self.get_current_patient_use_case = GetCurrentPatientUseCase(
            session_repository=self.patient_session_repository,
        )

    def _build_delivery_card_repository(self):
        if self.runtime_settings.repository_mode == "postgres":
            from src.infrastructure.persistence.db import build_session_factory
            from src.infrastructure.persistence.repositories import PostgresDeliveryCardRepository
            from src.infrastructure.persistence.settings import DatabaseSettings

            self._session_factory = build_session_factory(DatabaseSettings.from_env())
            return PostgresDeliveryCardRepository(session_factory=self._session_factory)
        self._session_factory = None
        return InMemoryDeliveryCardRepository()

    def _build_operator_audit_repository(self):
        if self._session_factory is None:
            return None
        from src.infrastructure.persistence.repositories import OperatorActionAuditRepository

        return OperatorActionAuditRepository(session_factory=self._session_factory)

    @staticmethod
    def build_seed_patients() -> dict[str, Patient]:
        """Возвращает in-memory карту пациентов для runtime-прогона."""

        return {
            "patient-001": Patient(
                id="patient-001",
                full_name="Иванов Иван Иванович",
                email="ivanov@example.org",
                phone="+79000000001",
            ),
            "patient-002": Patient(
                id="patient-002",
                full_name="Петрова Анна Сергеевна",
                email="petrova@example.org",
                phone="+79000000002",
            ),
            "patient-003": Patient(
                id="patient-003",
                full_name="Сидоров Пётр Алексеевич",
                email="sidorov@example.org",
                phone="+79000000003",
            ),
        }
