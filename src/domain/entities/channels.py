"""Каналы доставки результатов лабораторных исследований."""

from enum import StrEnum


class DeliveryChannel(StrEnum):
    """Доменное перечисление (value object), а не отдельная сущность.

    MAX — основной канал.
    EMAIL — резервный канал при недоступности/неуспехе основного.
    """

    MAX = "MAX"
    EMAIL = "EMAIL"
