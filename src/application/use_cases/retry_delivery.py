"""Use case повторной попытки доставки карточки."""

from src.application.interfaces import DeliveryProvider, NotificationLogger
from src.application.services.policies import DeliveryPolicy, RetryPolicy
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
        retry_policy: RetryPolicy,
        delivery_policy: DeliveryPolicy,
        register_result_use_case: RegisterDeliveryResultUseCase,
        failure_use_case: HandleDeliveryFailureUseCase,
        notification_logger: NotificationLogger | None = None,
    ) -> None:
        self._max_delivery_provider = max_delivery_provider
        self._email_delivery_provider = email_delivery_provider
        self._retry_policy = retry_policy
        self._delivery_policy = delivery_policy
        self._register_result_use_case = register_result_use_case
        self._failure_use_case = failure_use_case
        self._notification_logger = notification_logger

    def execute(self, card: DeliveryCard) -> DeliveryCard:
        before_send = self._delivery_policy.evaluate_before_send(card)
        if not before_send.can_send:
            return card

        retry_decision = self._retry_policy.evaluate(card)
        if not retry_decision.can_retry_now:
            return self._failure_use_case.execute(card)

        card.change_status(DeliveryStatus.NOT_STARTED)

        provider = self._max_delivery_provider if card.channel is DeliveryChannel.MAX else self._email_delivery_provider
        attempt = provider.send(card)
        updated_card = self._register_result_use_case.execute(card, attempt)

        if self._notification_logger is not None:
            self._notification_logger.log_attempt(updated_card, attempt)

        if attempt.result is AttemptStatus.ERROR:
            return self._failure_use_case.execute(updated_card)

        return updated_card
