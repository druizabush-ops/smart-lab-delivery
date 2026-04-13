"""Use case обработки неуспешной попытки доставки."""

from src.application.services.policies import DeliveryPolicy
from src.domain.entities import DeliveryCard
from src.domain.statuses import DeliveryStatus, QueueStatus


class HandleDeliveryFailureUseCase:
    """Применяет policy-решения после неуспешной попытки без отправки в канал."""

    def __init__(self, delivery_policy: DeliveryPolicy) -> None:
        self._delivery_policy = delivery_policy

    def execute(self, card: DeliveryCard) -> DeliveryCard:
        if card.status is not DeliveryStatus.FAILED:
            return card

        decision = self._delivery_policy.evaluate_after_failure(card)

        if decision.should_mark_exhausted:
            card.change_status(DeliveryStatus.EXHAUSTED)
            return card

        if decision.should_manual_review:
            card.change_queue_status(QueueStatus.MANUAL_REVIEW)
            return card

        if decision.next_channel is not None:
            card.channel = decision.next_channel
            card.change_status(DeliveryStatus.NOT_STARTED)
            return card

        card.change_queue_status(QueueStatus.WAITING_RETRY)
        return card
