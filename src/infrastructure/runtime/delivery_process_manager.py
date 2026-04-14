"""Синхронный process manager для управляемого execution lifecycle.

Назначение:
- объединить runtime cycle запуска новых READY результатов и reprocessing существующих карточек;
- обеспечить простой управляемый lifecycle без background scheduler и broker-инфраструктуры.
"""

from dataclasses import dataclass
import logging

from src.domain.entities import Patient
from src.infrastructure.runtime.delivery_runtime import DeliveryRuntime
from src.infrastructure.runtime.delivery_runtime_selector import DeliveryRuntimeSelector


@dataclass(frozen=True, slots=True)
class ProcessManagerSummary:
    """Сводка execution цикла process manager для локального operator/debug контроля."""

    new_cards_discovered: int
    existing_cards_reprocessed: int
    retry_candidates_count: int
    processed_count: int
    success_count: int
    failed_count: int
    manual_review_count: int
    exhausted_count: int


logger = logging.getLogger("sld.process_manager")


class DeliveryProcessManager:
    """Управляет жизненным циклом execution поверх DeliveryRuntime и persistence."""

    def __init__(self, runtime: DeliveryRuntime, selector: DeliveryRuntimeSelector) -> None:
        self._runtime = runtime
        self._selector = selector

    def run_once(self, patients: dict[str, Patient]) -> ProcessManagerSummary:
        """Запускает один цикл discovery READY результатов и их обработки."""

        created_ids = self._runtime.seed_ready_results(patients)
        logger.info("process_manager_run_once")
        run_summary = self._runtime.run_once(created_cards_count=len(created_ids))
        return ProcessManagerSummary(
            new_cards_discovered=len(created_ids),
            existing_cards_reprocessed=max(0, run_summary.processed_count - len(created_ids)),
            retry_candidates_count=0,
            processed_count=run_summary.processed_count,
            success_count=run_summary.success_count,
            failed_count=run_summary.failed_count,
            manual_review_count=run_summary.manual_review_count,
            exhausted_count=run_summary.exhausted_count,
        )

    def run_retry_cycle(self) -> ProcessManagerSummary:
        """Обрабатывает только retry-кандидатов, уже сохраненных в persistence."""

        retry_ids = self._selector.select_retry_candidate_ids()
        logger.info("process_manager_retry_cycle", extra={"processed_count": len(retry_ids)})
        self._runtime.enqueue_cards(retry_ids)
        run_summary = self._runtime.run_once(created_cards_count=0)

        return ProcessManagerSummary(
            new_cards_discovered=0,
            existing_cards_reprocessed=run_summary.processed_count,
            retry_candidates_count=len(retry_ids),
            processed_count=run_summary.processed_count,
            success_count=run_summary.success_count,
            failed_count=run_summary.failed_count,
            manual_review_count=run_summary.manual_review_count,
            exhausted_count=run_summary.exhausted_count,
        )

    def run_all_pending(self, patients: dict[str, Patient]) -> ProcessManagerSummary:
        """Обрабатывает новые READY результаты и все допустимые pending карточки."""

        created_ids = self._runtime.seed_ready_results(patients)
        logger.info("process_manager_run_once")
        pending_ids = self._selector.select_pending_card_ids(exclude_ids=set(created_ids))
        retry_candidates = set(self._selector.select_retry_candidate_ids())
        retry_count = len([card_id for card_id in pending_ids if card_id in retry_candidates])

        self._runtime.enqueue_cards(pending_ids)
        run_summary = self._runtime.run_once(created_cards_count=len(created_ids))

        return ProcessManagerSummary(
            new_cards_discovered=len(created_ids),
            existing_cards_reprocessed=max(0, run_summary.processed_count - len(created_ids)),
            retry_candidates_count=retry_count,
            processed_count=run_summary.processed_count,
            success_count=run_summary.success_count,
            failed_count=run_summary.failed_count,
            manual_review_count=run_summary.manual_review_count,
            exhausted_count=run_summary.exhausted_count,
        )
