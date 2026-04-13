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
from src.integration.delivery import EmailDeliveryProvider, MaxDeliveryProvider
from src.integration.logging import LoggerAdapter
from src.integration.renovatio import RenovatioClient


class AppContainer:
    """Собирает адаптеры integration-слоя и use case orchestration-слоя."""

    def __init__(self) -> None:
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
