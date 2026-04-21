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
from src.config.security_settings import SecuritySettings
from src.infrastructure.repositories import InMemoryDeliveryCardRepository
from src.infrastructure.session import InMemoryPatientSessionRepository
from src.integration.errors import IntegrationErrorKind, IntegrationFailure
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
        if patient_key == "pk-2":
            return {"patient_name": "Phone User", "patient_number": "p-1", "patient_id": "p-1"}
        raise ValueError("unknown patient key")

    def refresh_patient_key(self, patient_key: str, lifetime=None):
        return {"patient_key": f"{patient_key}-r"}


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


def test_login_me_refresh_logout_flow() -> None:
    client = TestClient(create_patient_api_app(container=_Container()))

    login = client.post("/patient/auth/login", json={"login": "demo", "password": "secret"})
    assert login.status_code == 200
    assert "patient_key" not in login.json()

    me = client.get("/patient/auth/me")
    assert me.status_code == 200
    assert me.json()["patient_number"] == "p-1"

    refresh = client.post("/patient/auth/refresh")
    assert refresh.status_code == 200

    logout = client.post("/patient/auth/logout")
    assert logout.status_code == 200

    me_after = client.get("/patient/auth/me")
    assert me_after.status_code == 401


def test_phone_flow_confirm_code() -> None:
    client = TestClient(create_patient_api_app(container=_Container()))
    start = client.post("/patient/auth/phone", json={"phone": "+79990000000"})
    assert start.status_code == 200
    assert start.json()["need_auth_key"] is True

    confirm = client.post("/patient/auth/confirm-code", json={"patient_id": "p-1", "code": "1234"})
    assert confirm.status_code == 200
    assert confirm.json()["auth_type"] == "phone"


def test_login_returns_controlled_error_when_profile_fetch_failed() -> None:
    class BrokenProfileStub(_RenovatioStub):
        def get_patient_info(self, patient_key: str):
            raise IntegrationFailure(IntegrationErrorKind.BAD_RESPONSE, "profile unavailable")

    class BrokenProfileContainer(_Container):
        def __init__(self):
            session_repo = InMemoryPatientSessionRepository()
            client = BrokenProfileStub()
            self.security_settings = SecuritySettings.from_env()
            self.renovatio_settings = type("RS", (), {"patient_key_lifetime_minutes": 120})()
            self.delivery_card_repository = InMemoryDeliveryCardRepository()
            self.patient_session_repository = session_repo
            self.patient_login_use_case = PatientLoginUseCase(client, session_repo, session_ttl_minutes=120, key_lifetime_minutes=120)
            self.patient_phone_login_use_case = PatientPhoneLoginUseCase(client)
            self.confirm_patient_auth_code_use_case = ConfirmPatientAuthCodeUseCase(client, session_repo, session_ttl_minutes=120)
            self.refresh_patient_session_use_case = RefreshPatientSessionUseCase(client, session_repo, session_ttl_minutes=120, key_lifetime_minutes=120)
            self.get_current_patient_use_case = GetCurrentPatientUseCase(session_repo)

    client = TestClient(create_patient_api_app(container=BrokenProfileContainer()))
    response = client.post("/patient/auth/login", json={"login": "demo", "password": "secret"})
    assert response.status_code == 502
    assert response.json()["code"] == "http_error"
    assert response.json()["message"] == "Не удалось получить профиль пациента"
