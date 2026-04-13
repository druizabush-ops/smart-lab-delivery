"""Тесты runtime/infrastructure in-memory контура."""

from src.config.container import AppContainer
from src.domain.entities import DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import LabResultStatus, QueueStatus
from src.infrastructure.queue import InMemoryDeliveryQueue
from src.infrastructure.repositories import InMemoryDeliveryCardRepository


def test_in_memory_repository_supports_crud_and_status_filter() -> None:
    patient = Patient(id="p-1", full_name="Test User", email="test@example.org")
    result = LabResult(id="lr-1", patient_id="p-1", status=LabResultStatus.READY)
    card = DeliveryCard.create(patient=patient, lab_result=result, channel=DeliveryChannel.MAX)

    repository = InMemoryDeliveryCardRepository()
    repository.save(card)

    card_id = repository.build_card_id(card)
    stored = repository.get_by_id(card_id)

    assert stored is not None
    assert stored.patient_id == "p-1"
    assert len(repository.list_all()) == 1
    assert len(repository.list_by_queue_status(QueueStatus.ACTIVE)) == 1


def test_in_memory_queue_is_fifo() -> None:
    queue = InMemoryDeliveryQueue()
    queue.enqueue("card-1")
    queue.enqueue("card-2")

    assert queue.size() == 2
    assert queue.dequeue() == "card-1"
    assert queue.dequeue() == "card-2"
    assert queue.dequeue() is None


def test_runtime_process_cycle_returns_summary_and_persists_cards() -> None:
    container = AppContainer()
    patients = container.build_seed_patients()

    summary = container.delivery_runtime.process_cycle(patients)

    assert summary.created_cards_count >= 1
    assert summary.processed_count == summary.created_cards_count
    assert summary.success_count >= 1
    assert len(container.delivery_card_repository.list_all()) == summary.created_cards_count
