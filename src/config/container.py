"""Простой wiring зависимостей без DI-фреймворков."""

from src.application.services import (
    DeduplicationPolicy,
    DeliveryPolicy,
    FallbackPolicy,
    RetryLimits,
    RetryPolicy,
)
from src.application.services.delivery_orchestrator import DeliveryOrchestrator
from src.application.use_cases import (
    CreateDeliveryCardUseCase,
    HandleDeliveryFailureUseCase,
    ProcessDeliveryUseCase,
    RegisterDeliveryResultUseCase,
    RetryDeliveryUseCase,
)
from src.domain.entities import Patient
from src.infrastructure.queue import InMemoryDeliveryQueue
from src.infrastructure.repositories import InMemoryDeliveryCardRepository
from src.config.runtime_settings import RuntimeSettings
from src.infrastructure.runtime import DeliveryRuntime
from src.integration.delivery import EmailDeliveryProvider, MaxDeliveryProvider
from src.integration.logging import LoggerAdapter
from src.integration.renovatio import RenovatioClient


class AppContainer:
    """Собирает интеграции, application use cases и runtime-контур исполнения."""

    def __init__(self) -> None:
        self.runtime_settings = RuntimeSettings.from_env()
        self.renovatio_client = RenovatioClient()
        self.max_delivery_provider = MaxDeliveryProvider()
        self.email_delivery_provider = EmailDeliveryProvider()
        self.notification_logger = LoggerAdapter()

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

        self.delivery_orchestrator = DeliveryOrchestrator(
            lab_result_provider=self.renovatio_client,
            create_delivery_card_use_case=self.create_delivery_card_use_case,
            process_delivery_use_case=self.process_delivery_use_case,
            retry_delivery_use_case=self.retry_delivery_use_case,
        )

        # Runtime / infrastructure wiring (dual-mode repository).
        self.delivery_card_repository = self._build_delivery_card_repository()
        self.delivery_queue = InMemoryDeliveryQueue()
        self.delivery_runtime = DeliveryRuntime(
            orchestrator=self.delivery_orchestrator,
            repository=self.delivery_card_repository,
            queue=self.delivery_queue,
        )


    def _build_delivery_card_repository(self):
        if self.runtime_settings.repository_mode == "postgres":
            from src.infrastructure.persistence.db import build_session_factory
            from src.infrastructure.persistence.repositories import PostgresDeliveryCardRepository
            from src.infrastructure.persistence.settings import DatabaseSettings

            session_factory = build_session_factory(DatabaseSettings.from_env())
            return PostgresDeliveryCardRepository(session_factory=session_factory)
        return InMemoryDeliveryCardRepository()

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
