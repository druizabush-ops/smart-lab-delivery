"""Статусы карточки в очереди обработки."""

from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python < 3.11 compatibility
    class StrEnum(str, Enum):
        """Совместимость со StrEnum для окружений Python 3.10."""



class QueueStatus(StrEnum):
    """Единый перечень операционных статусов очереди."""

    ACTIVE = "active"
    WAITING_RETRY = "waiting_retry"
    MANUAL_REVIEW = "manual_review"
    DONE = "done"
