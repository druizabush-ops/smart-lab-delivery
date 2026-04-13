"""In-memory очередь карточек доставки для синхронного runtime-цикла.

Назначение:
- предоставить прозрачную модель постановки карточек в обработку;
- не эмулировать message broker и не скрывать порядок обработки.
"""

from collections import deque


class InMemoryDeliveryQueue:
    """Простая FIFO-очередь идентификаторов карточек."""

    def __init__(self) -> None:
        self._items: deque[str] = deque()

    def enqueue(self, card_id: str) -> None:
        """Добавляет идентификатор карточки в хвост очереди."""

        self._items.append(card_id)

    def dequeue(self) -> str | None:
        """Возвращает следующий id из головы очереди или None при пустой очереди."""

        if not self._items:
            return None
        return self._items.popleft()

    def is_empty(self) -> bool:
        """Проверяет наличие элементов в очереди."""

        return not self._items

    def size(self) -> int:
        """Возвращает текущее число карточек в очереди."""

        return len(self._items)
