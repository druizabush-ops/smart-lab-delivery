"""Простой wiring зависимостей без DI-фреймворков."""

from src.application.services.delivery_orchestrator import DeliveryOrchestrator
from src.application.use_cases import (
    CreateDeliveryCardUseCase,
    ProcessDeliveryUseCase,
    RegisterDeliveryResultUseCase,
)
from src.integration.delivery import MaxDeliveryProvider
from src.integration.logging import LoggerAdapter
from src.integration.renovatio import RenovatioClient


class AppContainer:
    """Собирает адаптеры integration-слоя и use case orchestration-слоя."""

    def __init__(self) -> None:
        self.renovatio_client = RenovatioClient()
        self.delivery_provider = MaxDeliveryProvider()
        self.notification_logger = LoggerAdapter()

        self.create_delivery_card_use_case = CreateDeliveryCardUseCase()
        self.register_delivery_result_use_case = RegisterDeliveryResultUseCase()
        self.process_delivery_use_case = ProcessDeliveryUseCase(
            delivery_provider=self.delivery_provider,
            register_result_use_case=self.register_delivery_result_use_case,
            notification_logger=self.notification_logger,
        )

        self.delivery_orchestrator = DeliveryOrchestrator(
            lab_result_provider=self.renovatio_client,
            create_delivery_card_use_case=self.create_delivery_card_use_case,
            process_delivery_use_case=self.process_delivery_use_case,
        )
