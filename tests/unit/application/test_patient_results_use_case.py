from datetime import datetime, timedelta, timezone

import pytest

from src.application.use_cases.patient_auth import PatientSession
from src.application.use_cases.patient_results import (
    PatientLabResultNotFoundError,
    PatientResultsAccessError,
    PatientResultsUseCase,
)
from src.integration.errors import IntegrationErrorKind, IntegrationFailure


class _Sessions:
    def __init__(self, session: PatientSession | None):
        self._session = session

    def execute(self, session_id: str):
        if self._session and self._session.session_id == session_id:
            return self._session
        return None


class _Renovatio:
    def __init__(self):
        self.calls: list[tuple] = []

    def get_patient_lab_results_by_key(self, patient_key: str, *, lab_id=None, clinic_id=None):
        self.calls.append(("list", patient_key, lab_id, clinic_id))
        return [
            {
                "id": "r-1",
                "date": "2026-04-20",
                "datetime": "2026-04-20T11:10:00Z",
                "lab_id": "lab-1",
                "lab": "Основная лаб.",
                "clinic_id": "clinic-1",
                "clinic": "Центральная",
                "services": [{"name": "ОАК"}],
                "files": [{"id": "f-1", "name": "PDF", "url": "https://files/1.pdf"}],
            }
        ]

    def get_patient_lab_result_details_by_key(self, patient_key: str, result_id: str, *, lab_id=None, clinic_id=None):
        self.calls.append(("details", patient_key, result_id, lab_id, clinic_id))
        if result_id == "missing":
            raise IntegrationFailure(IntegrationErrorKind.EMPTY_RESULT, "not found")
        return {
            "id": result_id,
            "date": "2026-04-20",
            "datetime": "2026-04-20T11:10:00Z",
            "lab_id": "lab-1",
            "lab": "Основная лаб.",
            "clinic_id": "clinic-1",
            "clinic": "Центральная",
            "services": ["ОАК"],
            "sections": [{"name": "Гематология"}],
            "indicators": [{"name": "WBC", "value": "5.0"}],
            "documents": [{"id": "f-1", "title": "Бланк", "url": "https://files/1.pdf"}],
        }


def _session(active: bool = True, expired: bool = False) -> PatientSession:
    now = datetime.now(timezone.utc)
    return PatientSession(
        session_id="sid-1",
        patient_key="pk-1",
        patient_name="User",
        patient_number="P-1",
        created_at=now,
        expires_at=now - timedelta(minutes=1) if expired else now + timedelta(minutes=30),
        last_refresh_at=now,
        auth_type="login",
        is_active=active,
    )


def test_list_results_by_session_maps_payload_and_filters() -> None:
    client = _Renovatio()
    use_case = PatientResultsUseCase(sessions=_Sessions(_session()), renovatio_client=client)

    items = use_case.list_results_by_session(session_id="sid-1", lab_id="lab-1", clinic_id="clinic-1")

    assert len(items) == 1
    assert items[0].result_id == "r-1"
    assert items[0].services == ["ОАК"]
    assert items[0].files_count == 1
    assert client.calls[0] == ("list", "pk-1", "lab-1", "clinic-1")


@pytest.mark.parametrize("session", [None, _session(active=False), _session(expired=True)])
def test_list_results_by_session_requires_active_session(session: PatientSession | None) -> None:
    use_case = PatientResultsUseCase(sessions=_Sessions(session), renovatio_client=_Renovatio())

    with pytest.raises(PatientResultsAccessError):
        use_case.list_results_by_session(session_id="sid-1")


def test_get_result_details_by_session_maps_documents() -> None:
    client = _Renovatio()
    use_case = PatientResultsUseCase(sessions=_Sessions(_session()), renovatio_client=client)

    details = use_case.get_result_details_by_session(session_id="sid-1", result_id="r-1")

    assert details.result_id == "r-1"
    assert details.documents[0].readiness == "ready"
    assert details.sections[0]["name"] == "Гематология"


def test_get_result_details_by_session_returns_not_found() -> None:
    client = _Renovatio()
    use_case = PatientResultsUseCase(sessions=_Sessions(_session()), renovatio_client=client)

    with pytest.raises(PatientLabResultNotFoundError):
        use_case.get_result_details_by_session(session_id="sid-1", result_id="missing")
