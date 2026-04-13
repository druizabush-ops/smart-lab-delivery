"""Stub-адаптер логирования попыток доставки."""

from src.application.interfaces import NotificationLogger
from src.domain.entities import DeliveryAttempt, DeliveryCard


class LoggerAdapter(NotificationLogger):
    """Логирует попытки доставки в stdout."""

    def log_attempt(self, card: DeliveryCard, attempt: DeliveryAttempt) -> None:
        print(
            "[delivery-attempt] "
            f"patient_id={card.patient_id} "
            f"lab_result_id={card.lab_result_id} "
            f"channel={attempt.channel} "
            f"result={attempt.result} "
            f"error={attempt.error_message}"
        )
