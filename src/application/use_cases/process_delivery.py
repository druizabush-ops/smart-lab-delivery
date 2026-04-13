"""Use case оркестрации единичной отправки карточки доставки."""

from src.application.interfaces import DeliveryProvider, NotificationLogger
from src.application.use_cases.register_delivery_result import RegisterDeliveryResultUseCase
from src.domain.entities import DeliveryCard


class ProcessDeliveryUseCase:
    """Проверяет допустимость отправки и инициирует попытку через контракт провайдера."""

    def __init__(
        self,
        delivery_provider: DeliveryProvider,
        register_result_use_case: RegisterDeliveryResultUseCase,
        notification_logger: NotificationLogger | None = None,
    ) -> None:
        self._delivery_provider = delivery_provider
        self._register_result_use_case = register_result_use_case
        self._notification_logger = notification_logger

    def execute(self, card: DeliveryCard) -> DeliveryCard:
        """Обрабатывает карточку: send -> register result -> обновленный card."""

        if not card.can_be_sent():
            return card

        attempt = self._delivery_provider.send(card)
        updated_card = self._register_result_use_case.execute(card, attempt)

        if self._notification_logger is not None:
            self._notification_logger.log_attempt(updated_card, attempt)

        return updated_card
