"""Контракт провайдера доставки для application-слоя."""

from typing import Protocol

from src.domain.entities import DeliveryAttempt, DeliveryCard


class DeliveryProvider(Protocol):
    """Абстракция отправки карточки через внешний канал.

    Реализация в этом слое отсутствует: провайдер подставляется через DI.
    """

    def send(self, card: DeliveryCard) -> DeliveryAttempt:
        """Выполняет попытку отправки и возвращает терминальный результат попытки."""
