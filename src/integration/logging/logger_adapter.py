"""Инфраструктурный адаптер structured логирования попыток доставки."""

import logging

from src.application.interfaces import NotificationLogger
from src.domain.entities import DeliveryAttempt, DeliveryCard
from src.infrastructure.identity import build_operational_card_id


class LoggerAdapter(NotificationLogger):
    """Логирует попытки доставки структурированным логом."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("sld.delivery")

    def log_attempt(self, card: DeliveryCard, attempt: DeliveryAttempt) -> None:
        self._logger.info(
            "delivery_attempt",
            extra={
                "card_id": build_operational_card_id(card),
                "queue_status": card.queue_status.value,
                "command": "delivery_attempt",
                "success": attempt.error_message is None,
                "error": attempt.error_message,
            },
        )
