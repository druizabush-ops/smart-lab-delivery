import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from src.application.use_cases.patient_auth import (
    ConfirmPatientAuthCodeUseCase,
    GetCurrentPatientUseCase,
    PatientLoginUseCase,
    PatientPhoneLoginUseCase,
    RefreshPatientSessionUseCase,
)
from src.application.use_cases.patient_results import PatientResultPdfUseCase, PatientResultsUseCase
from src.config.security_settings import SecuritySettings
from src.infrastructure.repositories import InMemoryDeliveryCardRepository
from src.infrastructure.session import InMemoryPatientSessionRepository
from src.presentation.operator_api import create_operator_api_app
from src.presentation.patient_api import create_patient_api_app


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
        if patient_key == "pk-1":
            return {"patient_name": "Demo", "patient_number": "p-1", "patient_id": None}
        return {"patient_name": "Phone User", "patient_number": "p-1", "patient_id": "p-1"}

    def refresh_patient_key(self, patient_key: str, lifetime=None):
        return {"patient_key": f"{patient_key}-r"}


class _Container:
    def __init__(self) -> None:
        session_repo = InMemoryPatientSessionRepository()
        client = _RenovatioStub()
        self.delivery_card_repository = InMemoryDeliveryCardRepository()
        self.retry_delivery_card_command_use_case = None
        self.move_to_manual_review_command_use_case = None
        self.requeue_delivery_card_command_use_case = None
        self.override_channel_command_use_case = None
        self.security_settings = SecuritySettings.from_env()
        self.renovatio_settings = type("RS", (), {"patient_key_lifetime_minutes": 120})()
        self.patient_session_repository = session_repo
        self.patient_login_use_case = PatientLoginUseCase(client, session_repo, session_ttl_minutes=120, key_lifetime_minutes=120)
        self.patient_phone_login_use_case = PatientPhoneLoginUseCase(client)
        self.confirm_patient_auth_code_use_case = ConfirmPatientAuthCodeUseCase(client, session_repo, session_ttl_minutes=120)
        self.refresh_patient_session_use_case = RefreshPatientSessionUseCase(
            client, session_repo, session_ttl_minutes=120, key_lifetime_minutes=120
        )
        self.get_current_patient_use_case = GetCurrentPatientUseCase(session_repo)
        self.patient_results_use_case = PatientResultsUseCase(sessions=self.get_current_patient_use_case, renovatio_client=client)
        self.patient_result_pdf_use_case = PatientResultPdfUseCase(
            sessions=self.get_current_patient_use_case,
            renovatio_client=client,
        )

        class Runtime:
            repository_mode = "in_memory"
            integration_mode = "stub"
            environment = "test"

        self.runtime_settings = Runtime()


def test_health_endpoints_available() -> None:
    client = TestClient(create_operator_api_app(container=_Container()))

    live = client.get("/health/live")
    ready = client.get("/health/ready")

    assert live.status_code == 200
    assert ready.status_code == 200
    assert ready.json()["status"] in {"ready", "not_ready"}


def test_root_path_docs_and_openapi_available_for_nginx_prefixes() -> None:
    operator_client = TestClient(create_operator_api_app(container=_Container()))
    patient_client = TestClient(create_patient_api_app(container=_Container()))

    operator_docs = operator_client.get("/docs")
    patient_docs = patient_client.get("/docs")
    operator_openapi = operator_client.get("/openapi.json")
    patient_openapi = patient_client.get("/openapi.json")

    assert operator_docs.status_code == 200
    assert "/api/operator/openapi.json" in operator_docs.text
    assert patient_docs.status_code == 200
    assert "/api/patient/openapi.json" in patient_docs.text

    assert operator_openapi.status_code == 200
    assert patient_openapi.status_code == 200
    assert operator_openapi.json()["servers"][0]["url"] == "/api/operator"
    assert patient_openapi.json()["servers"][0]["url"] == "/api/patient"


def test_patient_endpoint_rejects_unsafe_context_in_strict_mode(monkeypatch) -> None:
    monkeypatch.setenv("SLD_PATIENT_SECURITY_MODE", "strict")
    client = TestClient(create_patient_api_app(container=_Container()))

    response = client.get("/patient/results", params={"patient_id": "patient-001"})

    assert response.status_code == 401
    assert response.json()["code"] == "http_error"
