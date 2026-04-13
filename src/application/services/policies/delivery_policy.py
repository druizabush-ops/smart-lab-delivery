"""Комбинированная delivery-политика на основе retry/fallback/dedup."""

from dataclasses import dataclass

from src.application.services.policies.deduplication_policy import DeduplicationPolicy
from src.application.services.policies.fallback_policy import FallbackPolicy
from src.application.services.policies.retry_policy import RetryPolicy
from src.domain.entities import DeliveryCard
from src.domain.statuses import DeliveryStatus, QueueStatus


@dataclass(frozen=True, slots=True)
class DeliveryDecision:
    """Итоговое решение перед попыткой отправки."""

    can_send: bool
    should_manual_review: bool
    should_mark_exhausted: bool
    reason: str


class DeliveryPolicy:
    """Единая точка принятия решений бизнес-логики доставки."""

    def __init__(
        self,
        retry_policy: RetryPolicy,
        fallback_policy: FallbackPolicy,
        deduplication_policy: DeduplicationPolicy,
    ) -> None:
        self._retry_policy = retry_policy
        self._fallback_policy = fallback_policy
        self._deduplication_policy = deduplication_policy

    def evaluate_before_send(self, card: DeliveryCard) -> DeliveryDecision:
        if not card.can_be_sent():
            return DeliveryDecision(False, False, False, "card_can_not_be_sent_now")

        dedup = self._deduplication_policy.evaluate(card)
        if not dedup.allow_send:
            return DeliveryDecision(False, False, False, dedup.reason)

        return DeliveryDecision(True, False, False, "send_allowed")

    def evaluate_after_failure(self, card: DeliveryCard) -> DeliveryDecision:
        retry_decision = self._retry_policy.evaluate(card)
        if retry_decision.should_mark_exhausted:
            return DeliveryDecision(False, False, True, retry_decision.reason)

        fallback_decision = self._fallback_policy.decide(card)
        if fallback_decision.should_manual_review:
            return DeliveryDecision(False, True, False, fallback_decision.reason)

        if fallback_decision.fallback_channel is not None:
            return DeliveryDecision(True, False, False, fallback_decision.reason)

        if retry_decision.can_retry_now:
            return DeliveryDecision(True, False, False, retry_decision.reason)

        if card.status is DeliveryStatus.FAILED and card.queue_status is QueueStatus.WAITING_RETRY:
            return DeliveryDecision(False, False, False, "failed_waiting_retry_is_temporary")

        return DeliveryDecision(False, True, False, "manual_review_by_default")
