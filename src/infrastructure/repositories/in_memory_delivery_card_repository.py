"""In-memory реализация репозитория карточек доставки.

Назначение:
- хранить операционное состояние карточек во время runtime-цикла;
- подготовить контракт для последующей замены на persistent-реализацию.
"""

from copy import deepcopy

from src.application.interfaces import DeliveryCardRepository
from src.domain.entities import DeliveryCard
from src.domain.statuses import QueueStatus
from src.infrastructure.identity import build_operational_card_id


class InMemoryDeliveryCardRepository(DeliveryCardRepository):
    """Операционное in-memory хранилище DeliveryCard по deterministic id."""

    def __init__(self) -> None:
        self._cards: dict[str, DeliveryCard] = {}

    def save(self, card: DeliveryCard) -> None:
        """Сохраняет карточку. Если id существует — заменяет запись."""

        self._cards[self._build_card_id(card)] = deepcopy(card)

    def update(self, card: DeliveryCard) -> None:
        """Обновляет карточку в хранилище; эквивалентно save для in-memory модели."""

        self.save(card)

    def get_by_id(self, card_id: str) -> DeliveryCard | None:
        """Возвращает карточку по id с защитой от внешней мутации."""

        card = self._cards.get(card_id)
        return deepcopy(card) if card is not None else None

    def list_all(self) -> list[DeliveryCard]:
        """Возвращает копии всех карточек."""

        return [deepcopy(card) for card in self._cards.values()]

    def list_by_queue_status(self, status: QueueStatus) -> list[DeliveryCard]:
        """Возвращает карточки, отфильтрованные по queue_status."""

        return [card for card in self.list_all() if card.queue_status is status]

    @staticmethod
    def build_card_id(card: DeliveryCard) -> str:
        """Публичный helper для вычисления операционного идентификатора карточки."""

        return InMemoryDeliveryCardRepository._build_card_id(card)

    @staticmethod
    def _build_card_id(card: DeliveryCard) -> str:
        return build_operational_card_id(card)
