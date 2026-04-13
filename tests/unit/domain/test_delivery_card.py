from datetime import datetime, timedelta

from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, DeliveryStatus, LabResultStatus, QueueStatus


def _ready_pair(patient_id: str = "p-1") -> tuple[Patient, LabResult]:
    patient = Patient(id=patient_id, full_name="Ivan Ivanov", email="ivan@example.com")
    result = LabResult(id="lr-1", patient_id=patient_id, status=LabResultStatus.READY)
    return patient, result


def test_delivery_card_create_factory_success() -> None:
    patient, result = _ready_pair()

    card = DeliveryCard.create(patient=patient, lab_result=result, channel=DeliveryChannel.MAX)

    assert card.patient_id == patient.id
    assert card.lab_result_id == result.id
    assert card.status is DeliveryStatus.NOT_STARTED
    assert card.queue_status is QueueStatus.ACTIVE


def test_delivery_card_create_for_non_ready_result_forbidden() -> None:
    patient = Patient(id="p-1", full_name="Ivan Ivanov")
    not_ready = LabResult(id="lr-1", patient_id="p-1", status=LabResultStatus.PENDING)

    try:
        DeliveryCard.create(patient=patient, lab_result=not_ready, channel=DeliveryChannel.MAX)
        assert False, "Expected ValueError for non-ready LabResult"
    except ValueError as exc:
        assert "только для LabResult" in str(exc)


def test_delivery_card_create_with_patient_result_mismatch_forbidden() -> None:
    patient = Patient(id="p-1", full_name="Ivan Ivanov")
    result = LabResult(id="lr-1", patient_id="p-2", status=LabResultStatus.READY)

    try:
        DeliveryCard.create(patient=patient, lab_result=result, channel=DeliveryChannel.MAX)
        assert False, "Expected ValueError for patient/result mismatch"
    except ValueError as exc:
        assert "patient.id" in str(exc)


def test_delivery_card_add_attempt_appends_history() -> None:
    patient, result = _ready_pair()
    card = DeliveryCard.create(patient=patient, lab_result=result, channel=DeliveryChannel.MAX)
    attempt = DeliveryAttempt(datetime.utcnow(), DeliveryChannel.MAX, AttemptStatus.ERROR, "tmp")

    card.add_attempt(attempt)

    assert len(card.attempts) == 1
    assert card.attempts[0] is attempt


def test_delivery_card_success_attempt_sets_success_status() -> None:
    patient, result = _ready_pair()
    card = DeliveryCard.create(patient=patient, lab_result=result, channel=DeliveryChannel.EMAIL)

    card.add_attempt(DeliveryAttempt(datetime.utcnow(), DeliveryChannel.EMAIL, AttemptStatus.SUCCESS))

    assert card.status is DeliveryStatus.EMAIL_SENT
    assert card.queue_status is QueueStatus.DONE


def test_delivery_card_error_attempt_sets_failed_status() -> None:
    patient, result = _ready_pair()
    card = DeliveryCard.create(patient=patient, lab_result=result, channel=DeliveryChannel.MAX)

    card.add_attempt(DeliveryAttempt(datetime.utcnow(), DeliveryChannel.MAX, AttemptStatus.ERROR, "err"))

    assert card.status is DeliveryStatus.FAILED
    assert card.queue_status is QueueStatus.WAITING_RETRY


def test_delivery_card_can_be_sent_consistent_with_statuses() -> None:
    patient, result = _ready_pair()
    card = DeliveryCard.create(patient=patient, lab_result=result, channel=DeliveryChannel.MAX)
    assert card.can_be_sent() is True

    card.change_status(DeliveryStatus.FAILED)
    assert card.queue_status is QueueStatus.WAITING_RETRY
    assert card.can_be_sent() is True

    card.change_queue_status(QueueStatus.MANUAL_REVIEW)
    assert card.can_be_sent() is False


def test_delivery_card_status_queue_transitions_follow_invariants() -> None:
    patient, result = _ready_pair()
    card = DeliveryCard.create(patient=patient, lab_result=result, channel=DeliveryChannel.MAX)

    card.change_status(DeliveryStatus.FAILED)
    card.change_status(DeliveryStatus.NOT_STARTED)
    assert card.queue_status is QueueStatus.ACTIVE

    card.change_status(DeliveryStatus.FAILED)
    card.change_status(DeliveryStatus.EXHAUSTED)
    assert card.queue_status is QueueStatus.DONE


def test_delivery_card_terminal_state_requires_done_queue_status() -> None:
    now = datetime.utcnow()
    try:
        DeliveryCard(
            patient_id="p-1",
            lab_result_id="lr-1",
            status=DeliveryStatus.MAX_SENT,
            queue_status=QueueStatus.ACTIVE,
            channel=DeliveryChannel.MAX,
            attempts=[],
            created_at=now,
            updated_at=now + timedelta(seconds=1),
        )
        assert False, "Expected ValueError for terminal status without DONE queue"
    except ValueError as exc:
        assert "queue_status" in str(exc)
