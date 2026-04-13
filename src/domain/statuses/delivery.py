"""Статусы процесса доставки результата пациенту."""

from enum import StrEnum


class DeliveryStatus(StrEnum):
    """Единый перечень статусов доставки для карточки."""

    NOT_STARTED = "not_started"
    MAX_SENT = "max_sent"
    EMAIL_SENT = "email_sent"
    FAILED = "failed"
    EXHAUSTED = "exhausted"
