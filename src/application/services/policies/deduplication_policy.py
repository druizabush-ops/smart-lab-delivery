"""Deduplication-политика защиты от повторной доставки."""

from dataclasses import dataclass

from src.domain.entities import DeliveryCard
from src.domain.statuses import AttemptStatus, DeliveryStatus


@dataclass(frozen=True, slots=True)
class DeduplicationDecision:
    """Решение дедупликации."""

    allow_send: bool
    reason: str


class DeduplicationPolicy:
    """Определяет, можно ли выполнять новую попытку без риска дублирования."""

    def evaluate(self, card: DeliveryCard) -> DeduplicationDecision:
        if card.status in {DeliveryStatus.MAX_SENT, DeliveryStatus.EMAIL_SENT}:
            return DeduplicationDecision(False, "already_delivered_successfully")

        if card.status is DeliveryStatus.EXHAUSTED:
            return DeduplicationDecision(False, "already_exhausted")

        has_success_attempt = any(attempt.result is AttemptStatus.SUCCESS for attempt in card.attempts)
        if has_success_attempt:
            return DeduplicationDecision(False, "successful_attempt_already_exists")

        return DeduplicationDecision(True, "send_allowed")
