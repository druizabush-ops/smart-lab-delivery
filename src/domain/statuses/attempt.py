"""Статусы результата отдельной попытки отправки."""

from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python < 3.11 compatibility
    class StrEnum(str, Enum):
        """Совместимость со StrEnum для окружений Python 3.10."""



class AttemptStatus(StrEnum):
    """Терминальные исходы единичной попытки доставки."""

    SUCCESS = "success"
    ERROR = "error"
