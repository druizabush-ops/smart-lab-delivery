"""Use case повторной попытки доставки карточки."""

from src.application.interfaces import DeliveryProvider, NotificationLogger
from src.application.services.policies import DeliveryPolicy
from src.application.use_cases.handle_delivery_failure import HandleDeliveryFailureUseCase
from src.application.use_cases.register_delivery_result import RegisterDeliveryResultUseCase
from src.domain.entities import DeliveryCard, DeliveryChannel
from src.domain.statuses import AttemptStatus, DeliveryStatus


class RetryDeliveryUseCase:
    """Выполняет retry-цикл, используя policy-объекты и провайдеры каналов."""

    def __init__(
        self,
        max_delivery_provider: DeliveryProvider,
        email_delivery_provider: DeliveryProvider,
        delivery_policy: DeliveryPolicy,
        register_result_use_case: RegisterDeliveryResultUseCase,
        failure_use_case: HandleDeliveryFailureUseCase,
        notification_logger: NotificationLogger | None = None,
    ) -> None:
        self._max_delivery_provider = max_delivery_provider
        self._email_delivery_provider = email_delivery_provider
        self._delivery_policy = delivery_policy
        self._register_result_use_case = register_result_use_case
        self._failure_use_case = failure_use_case
        self._notification_logger = notification_logger

    def execute(self, card: DeliveryCard) -> DeliveryCard:
        prepared_card = card
        if prepared_card.status is DeliveryStatus.FAILED:
            prepared_card = self._failure_use_case.execute(prepared_card)

        before_send = self._delivery_policy.evaluate_before_send(prepared_card)
        if not before_send.can_send:
            return prepared_card

        target_channel = before_send.next_channel or prepared_card.channel
        if target_channel is not prepared_card.channel:
            prepared_card.channel = target_channel

        if prepared_card.status is DeliveryStatus.FAILED:
            prepared_card.change_status(DeliveryStatus.NOT_STARTED)

        provider = self._max_delivery_provider if target_channel is DeliveryChannel.MAX else self._email_delivery_provider
        attempt = provider.send(prepared_card)
        updated_card = self._register_result_use_case.execute(prepared_card, attempt)

        if self._notification_logger is not None:
            self._notification_logger.log_attempt(updated_card, attempt)

        if attempt.result is AttemptStatus.ERROR:
            return self._failure_use_case.execute(updated_card)

        return updated_card
