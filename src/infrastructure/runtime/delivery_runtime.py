"""Runtime-исполнитель delivery flow поверх application/domain слоев.

Ограничения:
- слой не содержит retry/fallback/dedup business-правил;
- runtime только управляет последовательностью выполнения и сохранением состояния.
"""

from dataclasses import dataclass

from src.application.interfaces import DeliveryCardRepository
from src.application.services.delivery_orchestrator import DeliveryOrchestrator
from src.domain.entities import DeliveryCard, Patient
from src.domain.statuses import DeliveryStatus, QueueStatus
from src.infrastructure.identity import build_operational_card_id
from src.infrastructure.queue.in_memory_delivery_queue import InMemoryDeliveryQueue


@dataclass(frozen=True, slots=True)
class DeliveryRunSummary:
    """Сводка выполнения одного runtime-цикла для оператора и логов."""

    processed_count: int
    success_count: int
    failed_count: int
    manual_review_count: int
    exhausted_count: int
    created_cards_count: int
    retried_count: int


class DeliveryRuntime:
    """Синхронный runner доставки: seed -> queue -> processing -> summary."""

    def __init__(
        self,
        orchestrator: DeliveryOrchestrator,
        repository: DeliveryCardRepository,
        queue: InMemoryDeliveryQueue,
    ) -> None:
        self._orchestrator = orchestrator
        self._repository = repository
        self._queue = queue

    def seed_ready_results(self, patients: dict[str, Patient]) -> list[str]:
        """Создает карточки из ready результатов и ставит их в очередь обработки."""

        created_cards = self._orchestrator.orchestrate_ready_results(patients)
        card_ids: list[str] = []
        for card in created_cards:
            card_id = build_operational_card_id(card)
            self._repository.save(card)
            self._queue.enqueue(card_id)
            card_ids.append(card_id)
        return card_ids

    def enqueue_cards(self, card_ids: list[str]) -> None:
        """Добавляет существующие карточки в runtime-очередь для следующего цикла."""

        for card_id in card_ids:
            self._queue.enqueue(card_id)

    def run_once(self, *, created_cards_count: int = 0) -> DeliveryRunSummary:
        """Выполняет один полный прогон накопленной очереди карточек."""

        processed_count = 0
        success_count = 0
        failed_count = 0
        manual_review_count = 0
        exhausted_count = 0
        retried_count = 0

        while not self._queue.is_empty():
            card_id = self._queue.dequeue()
            if card_id is None:
                break

            card = self._repository.get_by_id(card_id)
            if card is None:
                continue

            previous_attempts = len(card.attempts)
            processed = self._process_card(card)
            self._repository.update(processed)
            processed_count += 1

            if len(processed.attempts) > previous_attempts:
                retried_count += 1

            if processed.status in {DeliveryStatus.MAX_SENT, DeliveryStatus.EMAIL_SENT}:
                success_count += 1
            elif processed.status is DeliveryStatus.EXHAUSTED:
                exhausted_count += 1

            if processed.queue_status is QueueStatus.MANUAL_REVIEW:
                manual_review_count += 1

            if processed.status is DeliveryStatus.FAILED:
                failed_count += 1

        return DeliveryRunSummary(
            processed_count=processed_count,
            success_count=success_count,
            failed_count=failed_count,
            manual_review_count=manual_review_count,
            exhausted_count=exhausted_count,
            created_cards_count=created_cards_count,
            retried_count=retried_count,
        )

    def process_cycle(self, patients: dict[str, Patient]) -> DeliveryRunSummary:
        """Выполняет цикл seed + run_once и возвращает финальную сводку."""

        created_ids = self.seed_ready_results(patients)
        return self.run_once(created_cards_count=len(created_ids))

    def _process_card(self, card: DeliveryCard) -> DeliveryCard:
        """Маршрутизирует карточку в primary/retry use case через orchestrator."""

        if card.status is DeliveryStatus.FAILED or card.queue_status is QueueStatus.WAITING_RETRY:
            return self._orchestrator.orchestrate_retry(card)
        return self._orchestrator.orchestrate_existing_card(card)
