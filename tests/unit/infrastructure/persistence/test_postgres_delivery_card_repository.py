import pytest

pytest.importorskip("sqlalchemy")

from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, LabResultStatus, QueueStatus
from src.infrastructure.identity import build_operational_card_id
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.repositories import PostgresDeliveryCardRepository


def _build_repository() -> PostgresDeliveryCardRepository:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    return PostgresDeliveryCardRepository(session_factory=factory)


def _build_card() -> DeliveryCard:
    patient = Patient(id="p-1", full_name="Test User", email="test@example.org")
    result = LabResult(id="lr-1", patient_id="p-1", status=LabResultStatus.READY)
    return DeliveryCard.create(patient=patient, lab_result=result, channel=DeliveryChannel.MAX)


def test_repository_save_get_update_and_attempts() -> None:
    repository = _build_repository()
    card = _build_card()

    repository.save(card)
    card_id = build_operational_card_id(card)

    loaded = repository.get_by_id(card_id)
    assert loaded is not None
    assert loaded.patient_id == card.patient_id

    attempt_time = loaded.created_at + timedelta(minutes=1)
    loaded.add_attempt(
        DeliveryAttempt(
            timestamp=attempt_time,
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.ERROR,
            error_message="timeout",
        )
    )
    repository.update(loaded)

    updated = repository.get_by_id(card_id)
    assert updated is not None
    assert len(updated.attempts) == 1
    assert updated.attempts[0].error_message == "timeout"
    assert repository.list_by_queue_status(QueueStatus.WAITING_RETRY)
