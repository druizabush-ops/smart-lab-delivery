"""Fallback-политика MAX -> EMAIL."""

from dataclasses import dataclass

from src.domain.entities import DeliveryCard, DeliveryChannel
from src.domain.statuses import DeliveryStatus, QueueStatus


@dataclass(frozen=True, slots=True)
class FallbackDecision:
    """Решение fallback-политики."""

    fallback_channel: DeliveryChannel | None
    should_manual_review: bool
    reason: str


class FallbackPolicy:
    """Контролирует переключение между каналами, исключая хаотичные переходы."""

    def decide(self, card: DeliveryCard) -> FallbackDecision:
        if card.status is not DeliveryStatus.FAILED:
            return FallbackDecision(None, False, "fallback_only_after_failed")

        if card.queue_status is QueueStatus.MANUAL_REVIEW:
            return FallbackDecision(None, True, "manual_review_already_set")

        if card.channel is DeliveryChannel.EMAIL:
            return FallbackDecision(None, True, "email_failed_requires_manual_review")

        if card.channel is not DeliveryChannel.MAX:
            return FallbackDecision(None, True, "unknown_channel_requires_manual_review")

        has_email_attempt = any(attempt.channel is DeliveryChannel.EMAIL for attempt in card.attempts)
        if has_email_attempt:
            return FallbackDecision(None, True, "repeat_fallback_forbidden")

        return FallbackDecision(DeliveryChannel.EMAIL, False, "fallback_to_email_allowed")
