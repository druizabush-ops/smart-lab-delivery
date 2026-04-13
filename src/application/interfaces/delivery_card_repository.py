"""Контракт репозитория карточек доставки.

Ограничения:
- Контракт хранится в application-слое, чтобы runtime/infrastructure могли
  подменять реализацию без изменения business/use-case модулей.
- Репозиторий не содержит policy-логики и не принимает бизнес-решения.
"""

from typing import Protocol

from src.domain.entities import DeliveryCard
from src.domain.statuses import QueueStatus


class DeliveryCardRepository(Protocol):
    """Абстракция операционного хранилища DeliveryCard."""

    def save(self, card: DeliveryCard) -> None:
        """Сохраняет новую карточку в хранилище."""

    def update(self, card: DeliveryCard) -> None:
        """Обновляет существующую карточку по ее идентификатору."""

    def get_by_id(self, card_id: str) -> DeliveryCard | None:
        """Возвращает карточку по id или None, если запись отсутствует."""

    def list_all(self) -> list[DeliveryCard]:
        """Возвращает все карточки в хранилище."""

    def list_by_queue_status(self, status: QueueStatus) -> list[DeliveryCard]:
        """Возвращает карточки с указанным queue_status."""
