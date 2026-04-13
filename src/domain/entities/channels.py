"""Каналы доставки результатов лабораторных исследований."""

from enum import StrEnum


class DeliveryChannel(StrEnum):
    """Разрешенные каналы доставки.

    MAX — основной канал.
    EMAIL — резервный канал при недоступности/неуспехе основного.
    """

    MAX = "MAX"
    EMAIL = "EMAIL"
