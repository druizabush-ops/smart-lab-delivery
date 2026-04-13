from src.domain.entities import LabResult
from src.domain.statuses import LabResultStatus


def test_lab_result_valid_creation() -> None:
    result = LabResult(id="lr-1", patient_id="p-1", status=LabResultStatus.PENDING)

    assert result.id == "lr-1"
    assert result.patient_id == "p-1"
    assert result.status is LabResultStatus.PENDING


def test_lab_result_empty_id_raises_error() -> None:
    try:
        LabResult(id="", patient_id="p-1", status=LabResultStatus.PENDING)
        assert False, "Expected ValueError for empty id"
    except ValueError as exc:
        assert "Идентификатор результата" in str(exc)


def test_lab_result_empty_patient_id_raises_error() -> None:
    try:
        LabResult(id="lr-1", patient_id="", status=LabResultStatus.PENDING)
        assert False, "Expected ValueError for empty patient_id"
    except ValueError as exc:
        assert "Идентификатор пациента" in str(exc)


def test_lab_result_allows_valid_transitions() -> None:
    pending = LabResult(id="lr-1", patient_id="p-1", status=LabResultStatus.PENDING)

    ready = pending.change_status(LabResultStatus.READY)
    blocked = ready.change_status(LabResultStatus.BLOCKED)

    assert ready.status is LabResultStatus.READY
    assert blocked.status is LabResultStatus.BLOCKED


def test_lab_result_forbids_invalid_transitions() -> None:
    pending = LabResult(id="lr-1", patient_id="p-1", status=LabResultStatus.PENDING)

    try:
        pending.change_status(LabResultStatus.MISSING_PDF)
        assert False, "Expected ValueError for invalid transition"
    except ValueError as exc:
        assert "Запрещенный переход" in str(exc)
