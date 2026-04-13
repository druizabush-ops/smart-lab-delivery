"""Каналы доставки результатов лабораторных исследований."""

from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python < 3.11 compatibility
    class StrEnum(str, Enum):
        """Совместимость со StrEnum для окружений Python 3.10."""



class DeliveryChannel(StrEnum):
    """Доменное перечисление (value object), а не отдельная сущность.

    MAX — основной канал.
    EMAIL — резервный канал при недоступности/неуспехе основного.
    """

    MAX = "MAX"
    EMAIL = "EMAIL"
