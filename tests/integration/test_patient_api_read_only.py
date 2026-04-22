import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from src.application.use_cases.patient_auth import (
    BindPatientSessionUseCase,
    ConfirmPatientAuthCodeUseCase,
    GetCurrentPatientUseCase,
    PatientLoginUseCase,
    PatientPhoneLoginUseCase,
    RefreshPatientSessionUseCase,
    ResolveBoundPatientSessionUseCase,
    UnbindPatientSessionUseCase,
)
from src.application.use_cases.patient_results import PatientResultsUseCase
from src.application.use_cases.patient_results import PatientResultPdfUseCase
from src.config.security_settings import SecuritySettings
from src.infrastructure.repositories import InMemoryDeliveryCardRepository
from src.infrastructure.session import InMemoryExternalPatientBindingRepository, InMemoryPatientSessionRepository
from src.integration.errors import IntegrationErrorKind, IntegrationFailure
from src.presentation.patient_api import create_patient_api_app
import base64


class _RenovatioStub:
    def auth_patient_by_login(self, login: str, password: str, lifetime=None):
        if login != "demo" or password != "secret":
            raise ValueError("bad creds")
        return {"patient_key": "pk-1", "patient_id": None, "need_auth_key": 0}

    def auth_patient_by_phone(self, phone: str, lifetime=None):
        return {"need_auth_key": 1, "patient_id": "p-1"}

    def check_auth_code(self, patient_id: str, code: str):
        if code != "1234":
            raise ValueError("bad code")
        return {"patient_key": "pk-2", "patient_id": patient_id}

    def get_patient_info(self, patient_key: str):
        return {"number": "p-1", "full_name": "User One", "patient_id": None}

    def refresh_patient_key(self, patient_key: str, lifetime=None):
        return {"patient_key": f"{patient_key}-r"}

    def get_patient_lab_results_by_key(self, patient_key: str, *, lab_id=None, clinic_id=None):
        assert patient_key.startswith("pk-")
        return [
            {
                "id": "r-1",
                "date": "2026-04-20",
                "datetime": "2026-04-20T11:10:00Z",
                "lab_id": lab_id or "lab-default",
                "lab": "Lab",
                "clinic_id": clinic_id or "clinic-default",
                "clinic": "Clinic",
                "services": ["ОАК"],
                "documents": [{"id": "d-1", "title": "PDF", "url": "https://file/1.pdf"}],
            }
        ]

    def get_patient_lab_result_details_by_key(self, patient_key: str, result_id: str, *, lab_id=None, clinic_id=None):
        if result_id == "missing":
            raise IntegrationFailure(IntegrationErrorKind.EMPTY_RESULT, "not found")
        files: list[str] = []
        if result_id != "without-pdf":
            files = [base64.b64encode(b"%PDF-1.3\nstub-pdf\n%%EOF").decode("ascii")]
        return {
            "id": result_id,
            "date": "2026-04-20",
            "datetime": "2026-04-20T11:10:00Z",
            "lab_id": lab_id or "lab-default",
            "lab": "Lab",
            "clinic_id": clinic_id or "clinic-default",
            "clinic": "Clinic",
            "services": ["ОАК"],
            "sections": [{"name": "Section"}],
            "indicators": [{"name": "WBC", "value": "5.0"}],
            "documents": [{"id": "d-1", "title": "PDF", "url": "https://file/1.pdf"}],
            "files": files,
        }


class _Container:
    def __init__(self):
        session_repo = InMemoryPatientSessionRepository()
        client = _RenovatioStub()
        self.security_settings = SecuritySettings.from_env()
        self.renovatio_settings = type("RS", (), {"patient_key_lifetime_minutes": 120})()
        self.delivery_card_repository = InMemoryDeliveryCardRepository()
        self.patient_session_repository = session_repo
        self.patient_login_use_case = PatientLoginUseCase(client, session_repo, session_ttl_minutes=120, key_lifetime_minutes=120)
        self.patient_phone_login_use_case = PatientPhoneLoginUseCase(client)
        self.confirm_patient_auth_code_use_case = ConfirmPatientAuthCodeUseCase(client, session_repo, session_ttl_minutes=120)
        self.refresh_patient_session_use_case = RefreshPatientSessionUseCase(client, session_repo, session_ttl_minutes=120, key_lifetime_minutes=120)
        self.get_current_patient_use_case = GetCurrentPatientUseCase(session_repo)
        self.patient_results_use_case = PatientResultsUseCase(sessions=self.get_current_patient_use_case, renovatio_client=client)
        self.patient_result_pdf_use_case = PatientResultPdfUseCase(sessions=self.get_current_patient_use_case, renovatio_client=client)
        bindings = InMemoryExternalPatientBindingRepository()
        self.bind_patient_session_use_case = BindPatientSessionUseCase(bindings)
        self.resolve_bound_patient_session_use_case = ResolveBoundPatientSessionUseCase(bindings)
        self.unbind_patient_session_use_case = UnbindPatientSessionUseCase(bindings)


def _login(client: TestClient) -> None:
    response = client.post("/patient/auth/login", json={"login": "demo", "password": "secret"})
    assert response.status_code == 200


def test_results_list_and_detail_via_server_side_session() -> None:
    client = TestClient(create_patient_api_app(container=_Container()))
    _login(client)

    list_response = client.get("/patient/results", params={"patient_id": "foreign", "lab_id": "lab-1", "clinic_id": "clinic-1"})
    assert list_response.status_code == 200
    payload = list_response.json()
    assert len(payload) == 1
    assert payload[0]["result_id"] == "r-1"
    assert payload[0]["has_pdf"] is True
    assert payload[0]["title"]

    details = client.get("/patient/results/r-1", params={"patient_id": "foreign", "lab_id": "lab-1", "clinic_id": "clinic-1"})
    assert details.status_code == 200
    assert details.json()["has_pdf"] is True
    assert details.json()["pdf_open_url"] == "/patient/results/r-1/pdf"


def test_results_endpoints_require_session() -> None:
    client = TestClient(create_patient_api_app(container=_Container()))

    list_response = client.get("/patient/results", params={"patient_id": "foreign"})
    details_response = client.get("/patient/results/r-1", params={"patient_id": "foreign"})

    assert list_response.status_code == 401
    assert details_response.status_code == 401


def test_result_details_not_found_returns_404() -> None:
    client = TestClient(create_patient_api_app(container=_Container()))
    _login(client)

    response = client.get("/patient/results/missing")

    assert response.status_code == 404


def test_result_pdf_download_via_server_side_session() -> None:
    client = TestClient(create_patient_api_app(container=_Container()))
    _login(client)

    response = client.get("/patient/results/r-1/pdf")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert "attachment; filename=\"result-r-1.pdf\"" == response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_result_pdf_open_inline_disposition_via_query() -> None:
    client = TestClient(create_patient_api_app(container=_Container()))
    _login(client)

    response = client.get("/patient/results/r-1/pdf", params={"disposition": "inline"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert "inline; filename=\"result-r-1.pdf\"" == response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_result_pdf_requires_session() -> None:
    client = TestClient(create_patient_api_app(container=_Container()))
    response = client.get("/patient/results/r-1/pdf")
    assert response.status_code == 401


def test_result_pdf_not_available_returns_404() -> None:
    client = TestClient(create_patient_api_app(container=_Container()))
    _login(client)

    response = client.get("/patient/results/without-pdf/pdf")

    assert response.status_code == 404
