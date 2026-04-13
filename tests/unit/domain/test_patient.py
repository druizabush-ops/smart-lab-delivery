from src.domain.entities import Patient


def test_patient_valid_creation() -> None:
    patient = Patient(id="p-1", full_name="Ivan Ivanov", email="ivan@example.com")

    assert patient.id == "p-1"
    assert patient.full_name == "Ivan Ivanov"
    assert patient.email == "ivan@example.com"


def test_patient_empty_id_raises_error() -> None:
    try:
        Patient(id="  ", full_name="Ivan Ivanov")
        assert False, "Expected ValueError for empty id"
    except ValueError as exc:
        assert "Идентификатор пациента" in str(exc)


def test_patient_empty_full_name_raises_error() -> None:
    try:
        Patient(id="p-1", full_name="  ")
        assert False, "Expected ValueError for empty full_name"
    except ValueError as exc:
        assert "ФИО пациента" in str(exc)


def test_patient_invalid_email_raises_error_when_email_set() -> None:
    try:
        Patient(id="p-1", full_name="Ivan Ivanov", email="invalid-email")
        assert False, "Expected ValueError for invalid email"
    except ValueError as exc:
        assert "Email" in str(exc)
