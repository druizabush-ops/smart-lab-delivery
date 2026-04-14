"""Selection/query слой кандидатов для runtime process manager.

Ограничения:
- селектор не принимает бизнес-решений retry/fallback/dedup;
- селектор только отбирает карточки по операционным статусам из repository.
"""

from src.application.interfaces import DeliveryCardRepository
from src.domain.statuses import DeliveryStatus, QueueStatus
from src.infrastructure.identity import build_operational_card_id


class DeliveryRuntimeSelector:
    """Выбирает карточки-кандидаты для execution lifecycle циклов."""

    def __init__(self, repository: DeliveryCardRepository) -> None:
        self._repository = repository

    def select_retry_candidate_ids(self) -> list[str]:
        """Возвращает id карточек, подходящих для retry-цикла."""

        candidates: list[str] = []
        for card in self._repository.list_all():
            if card.queue_status is QueueStatus.WAITING_RETRY:
                candidates.append(build_operational_card_id(card))
                continue

            if (
                card.status is DeliveryStatus.FAILED
                and card.queue_status not in {QueueStatus.DONE, QueueStatus.MANUAL_REVIEW}
            ):
                candidates.append(build_operational_card_id(card))

        return candidates

    def select_pending_card_ids(self, *, exclude_ids: set[str] | None = None) -> list[str]:
        """Возвращает id всех runtime-кандидатов для полного pending-цикла."""

        excluded = exclude_ids or set()
        pending: list[str] = []

        for card in self._repository.list_all():
            card_id = build_operational_card_id(card)
            if card_id in excluded:
                continue

            if card.queue_status in {QueueStatus.DONE, QueueStatus.MANUAL_REVIEW}:
                continue

            if card.status is DeliveryStatus.EXHAUSTED:
                continue

            pending.append(card_id)

        return pending
