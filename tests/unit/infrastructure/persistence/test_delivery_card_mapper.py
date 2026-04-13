import pytest

pytest.importorskip("sqlalchemy")

from datetime import datetime, timedelta

from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, LabResultStatus
from src.infrastructure.identity import build_operational_card_id
from src.infrastructure.persistence.mappers import DeliveryCardMapper


def test_delivery_card_mapper_roundtrip_preserves_attempts_and_statuses() -> None:
    patient = Patient(id="p-1", full_name="Test User", email="test@example.org")
    result = LabResult(id="lr-1", patient_id="p-1", status=LabResultStatus.READY)
    created_at = datetime(2026, 4, 13, 10, 0, 0)

    card = DeliveryCard.create(
        patient=patient,
        lab_result=result,
        channel=DeliveryChannel.MAX,
        created_at=created_at,
    )
    card.add_attempt(
        DeliveryAttempt(
            timestamp=created_at + timedelta(minutes=1),
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.ERROR,
            error_message="MAX timeout",
        )
    )

    model = DeliveryCardMapper.to_model(build_operational_card_id(card), card)
    restored = DeliveryCardMapper.to_domain(model)

    assert restored.patient_id == card.patient_id
    assert restored.lab_result_id == card.lab_result_id
    assert restored.status == card.status
    assert restored.queue_status == card.queue_status
    assert len(restored.attempts) == 1
    assert restored.attempts[0].error_message == "MAX timeout"
