"""Статусы процесса доставки результата пациенту."""

from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python < 3.11 compatibility
    class StrEnum(str, Enum):
        """Совместимость со StrEnum для окружений Python 3.10."""



class DeliveryStatus(StrEnum):
    """Единый перечень статусов доставки для карточки."""

    NOT_STARTED = "not_started"
    MAX_SENT = "max_sent"
    EMAIL_SENT = "email_sent"
    FAILED = "failed"
    EXHAUSTED = "exhausted"
