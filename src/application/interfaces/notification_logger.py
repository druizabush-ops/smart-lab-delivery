"""Опциональный контракт логирования попыток доставки."""

from typing import Protocol

from src.domain.entities import DeliveryAttempt, DeliveryCard


class NotificationLogger(Protocol):
    """Абстракция журналирования без привязки к конкретной системе логов."""

    def log_attempt(self, card: DeliveryCard, attempt: DeliveryAttempt) -> None:
        """Логирует результат попытки доставки."""
