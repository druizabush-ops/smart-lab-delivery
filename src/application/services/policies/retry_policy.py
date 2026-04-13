"""Retry-политика для карточек доставки."""

from dataclasses import dataclass

from src.domain.entities import DeliveryCard, DeliveryChannel
from src.domain.statuses import DeliveryStatus, QueueStatus


@dataclass(frozen=True, slots=True)
class RetryLimits:
    """Явные лимиты retry без магических чисел в use cases."""

    max_total_attempts: int = 4
    max_max_attempts: int = 2
    max_email_attempts: int = 2


@dataclass(frozen=True, slots=True)
class RetryDecision:
    """Решение retry-политики."""

    can_retry_now: bool
    should_wait_retry: bool
    should_mark_exhausted: bool
    reason: str


class RetryPolicy:
    """Определяет допустимость и пределы повторных попыток доставки."""

    def __init__(self, limits: RetryLimits | None = None) -> None:
        self._limits = limits or RetryLimits()

    def evaluate(self, card: DeliveryCard) -> RetryDecision:
        total_attempts = len(card.attempts)
        max_attempts = self._count_attempts(card, DeliveryChannel.MAX)
        email_attempts = self._count_attempts(card, DeliveryChannel.EMAIL)

        if card.status in {DeliveryStatus.MAX_SENT, DeliveryStatus.EMAIL_SENT, DeliveryStatus.EXHAUSTED}:
            return RetryDecision(False, False, False, "retry_forbidden_for_terminal_status")

        if card.status is not DeliveryStatus.FAILED:
            return RetryDecision(False, False, False, "retry_only_after_failed")

        if total_attempts >= self._limits.max_total_attempts:
            return RetryDecision(False, False, True, "total_attempts_exhausted")

        if card.channel is DeliveryChannel.MAX and max_attempts >= self._limits.max_max_attempts:
            return RetryDecision(False, False, False, "max_channel_limit_reached")

        if card.channel is DeliveryChannel.EMAIL and email_attempts >= self._limits.max_email_attempts:
            return RetryDecision(False, False, True, "email_channel_limit_reached")

        if card.queue_status is QueueStatus.MANUAL_REVIEW:
            return RetryDecision(False, False, False, "manual_review_required")

        return RetryDecision(True, True, False, "retry_allowed")

    @staticmethod
    def _count_attempts(card: DeliveryCard, channel: DeliveryChannel) -> int:
        return sum(1 for attempt in card.attempts if attempt.channel is channel)
