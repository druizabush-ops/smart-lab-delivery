"""Тесты scheduler/process manager слоя и runtime selection logic."""

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.config.container import AppContainer
from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, DeliveryStatus, LabResultStatus, QueueStatus
from src.infrastructure.identity import build_operational_card_id
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.repositories import PostgresDeliveryCardRepository
from src.infrastructure.repositories import InMemoryDeliveryCardRepository
from src.infrastructure.runtime import DeliveryRunSummary, DeliveryRuntimeSelector
from src.infrastructure.runtime.delivery_process_manager import DeliveryProcessManager


class StubRuntime:
    """Тестовый runtime-двойник для проверки orchestration process manager."""

    def __init__(self, seed_ids: list[str] | None = None) -> None:
        self.seed_ids = seed_ids or []
        self.enqueued_ids: list[str] = []

    def seed_ready_results(self, patients) -> list[str]:  # noqa: ANN001
        return list(self.seed_ids)

    def enqueue_cards(self, card_ids: list[str]) -> None:
        self.enqueued_ids.extend(card_ids)

    def run_once(self, *, created_cards_count: int = 0) -> DeliveryRunSummary:
        processed_count = created_cards_count + len(self.enqueued_ids)
        return DeliveryRunSummary(
            processed_count=processed_count,
            success_count=processed_count,
            failed_count=0,
            manual_review_count=0,
            exhausted_count=0,
            created_cards_count=created_cards_count,
            retried_count=len(self.enqueued_ids),
        )


def _build_card(patient_id: str, lab_result_id: str) -> DeliveryCard:
    patient = Patient(id=patient_id, full_name="Test User", email="test@example.org")
    result = LabResult(id=lab_result_id, patient_id=patient_id, status=LabResultStatus.READY)
    return DeliveryCard.create(patient=patient, lab_result=result, channel=DeliveryChannel.MAX)


def _mark_failed(card: DeliveryCard) -> None:
    card.add_attempt(
        DeliveryAttempt(
            timestamp=datetime.utcnow(),
            channel=card.channel,
            result=AttemptStatus.ERROR,
            error_message="network",
        )
    )


def test_runtime_selector_filters_pending_and_retry_cards() -> None:
    repository = InMemoryDeliveryCardRepository()

    waiting_retry = _build_card("p-wait", "lr-wait")
    _mark_failed(waiting_retry)
    repository.save(waiting_retry)

    active_card = _build_card("p-active", "lr-active")
    repository.save(active_card)

    done_card = _build_card("p-done", "lr-done")
    done_card.add_attempt(
        DeliveryAttempt(
            timestamp=datetime.utcnow(),
            channel=done_card.channel,
            result=AttemptStatus.SUCCESS,
        )
    )
    repository.save(done_card)

    manual_review = _build_card("p-manual", "lr-manual")
    _mark_failed(manual_review)
    manual_review.change_queue_status(QueueStatus.MANUAL_REVIEW)
    repository.save(manual_review)

    exhausted = _build_card("p-exhausted", "lr-exhausted")
    _mark_failed(exhausted)
    exhausted.change_status(DeliveryStatus.EXHAUSTED)
    repository.save(exhausted)

    selector = DeliveryRuntimeSelector(repository)

    retry_ids = set(selector.select_retry_candidate_ids())
    pending_ids = set(selector.select_pending_card_ids())

    waiting_id = build_operational_card_id(waiting_retry)
    active_id = build_operational_card_id(active_card)

    assert retry_ids == {waiting_id}
    assert waiting_id in pending_ids
    assert active_id in pending_ids
    assert build_operational_card_id(done_card) not in pending_ids
    assert build_operational_card_id(manual_review) not in pending_ids
    assert build_operational_card_id(exhausted) not in pending_ids


def test_process_manager_run_retry_cycle_processes_only_retry_candidates() -> None:
    repository = InMemoryDeliveryCardRepository()

    waiting_retry = _build_card("p-retry", "lr-retry")
    _mark_failed(waiting_retry)
    repository.save(waiting_retry)

    done_card = _build_card("p-done", "lr-done")
    done_card.add_attempt(
        DeliveryAttempt(
            timestamp=datetime.utcnow(),
            channel=done_card.channel,
            result=AttemptStatus.SUCCESS,
        )
    )
    repository.save(done_card)

    selector = DeliveryRuntimeSelector(repository)
    runtime = StubRuntime()
    manager = DeliveryProcessManager(runtime=runtime, selector=selector)

    summary = manager.run_retry_cycle()

    assert runtime.enqueued_ids == [build_operational_card_id(waiting_retry)]
    assert summary.retry_candidates_count == 1
    assert summary.new_cards_discovered == 0
    assert summary.existing_cards_reprocessed == 1
    assert summary.processed_count == 1


def test_process_manager_run_once_keeps_single_cycle_behavior() -> None:
    container = AppContainer()

    summary = container.delivery_process_manager.run_once(container.build_seed_patients())

    assert summary.new_cards_discovered >= 1
    assert summary.processed_count == summary.new_cards_discovered
    assert summary.existing_cards_reprocessed == 0


def test_runtime_selector_works_with_postgres_repository_mode() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)

    repository = PostgresDeliveryCardRepository(session_factory=factory)

    waiting_retry = _build_card("p-postgres", "lr-postgres")
    _mark_failed(waiting_retry)
    repository.save(waiting_retry)

    selector = DeliveryRuntimeSelector(repository)

    retry_ids = selector.select_retry_candidate_ids()

    assert retry_ids == [build_operational_card_id(waiting_retry)]
