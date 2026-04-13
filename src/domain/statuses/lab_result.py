"""Статусы готовности лабораторного результата."""

from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python < 3.11 compatibility
    class StrEnum(str, Enum):
        """Совместимость со StrEnum для окружений Python 3.10."""



class LabResultStatus(StrEnum):
    """Единый перечень статусов лабораторного результата."""

    PENDING = "pending"
    READY = "ready"
    MISSING_PDF = "missing_pdf"
    BLOCKED = "blocked"
