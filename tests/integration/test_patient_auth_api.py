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

from src.application.use_cases.bot_patient import (
    BotCheckLoginUseCase,
    BotMiniAppTokenUseCase,
    BotProfileCipher,
    BotProfileUseCase,
    InMemoryBotPatientProfileRepository,
)
from src.config.security_settings import SecuritySettings
from src.infrastructure.repositories import InMemoryDeliveryCardRepository
from src.infrastructure.session import InMemoryExternalPatientBindingRepository, InMemoryPatientSessionRepository
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
            return {"number": "p-1", "last_name": "Иванов", "first_name": "Иван", "third_name": "Иванович", "patient_id": None}
        if patient_key == "pk-2":
            return {"number": "p-1", "full_name": "Phone User", "patient_id": "p-1"}
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
        self.patient_results_use_case = PatientResultsUseCase(sessions=self.get_current_patient_use_case, renovatio_client=client)
        self.patient_result_pdf_use_case = PatientResultPdfUseCase(sessions=self.get_current_patient_use_case, renovatio_client=client)
        bindings = InMemoryExternalPatientBindingRepository()
        self.bind_patient_session_use_case = BindPatientSessionUseCase(bindings)
        self.resolve_bound_patient_session_use_case = ResolveBoundPatientSessionUseCase(bindings)
        self.unbind_patient_session_use_case = UnbindPatientSessionUseCase(bindings)
        bot_repository = InMemoryBotPatientProfileRepository()
        bot_profile = BotProfileUseCase(bot_repository, BotProfileCipher("test-encryption-key"))
        self.bot_profile_use_case = bot_profile
        self.bot_check_login_use_case = BotCheckLoginUseCase(
            profiles=bot_profile,
            patient_login_use_case=self.patient_login_use_case,
            repository=bot_repository,
        )
        self.bot_miniapp_token_use_case = BotMiniAppTokenUseCase(bot_repository)


def test_login_me_refresh_logout_flow() -> None:
    client = TestClient(create_patient_api_app(container=_Container()))

    login = client.post("/patient/auth/login", json={"login": "demo", "password": "secret"})
    assert login.status_code == 200
    assert "patient_key" not in login.json()

    me = client.get("/patient/auth/me")
    assert me.status_code == 200
    assert me.json()["patient_number"] == "p-1"
    assert me.json()["patient_name"] == "Иванов Иван Иванович"

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
            self.patient_results_use_case = PatientResultsUseCase(sessions=self.get_current_patient_use_case, renovatio_client=client)
            self.patient_result_pdf_use_case = PatientResultPdfUseCase(sessions=self.get_current_patient_use_case, renovatio_client=client)
            bindings = InMemoryExternalPatientBindingRepository()
            self.bind_patient_session_use_case = BindPatientSessionUseCase(bindings)
            self.resolve_bound_patient_session_use_case = ResolveBoundPatientSessionUseCase(bindings)
            self.unbind_patient_session_use_case = UnbindPatientSessionUseCase(bindings)
            bot_repository = InMemoryBotPatientProfileRepository()
            bot_profile = BotProfileUseCase(bot_repository, BotProfileCipher("test-encryption-key"))
            self.bot_profile_use_case = bot_profile
            self.bot_check_login_use_case = BotCheckLoginUseCase(
            profiles=bot_profile,
            patient_login_use_case=self.patient_login_use_case,
            repository=bot_repository,
            )
            self.bot_miniapp_token_use_case = BotMiniAppTokenUseCase(bot_repository)

    client = TestClient(create_patient_api_app(container=BrokenProfileContainer()))
    response = client.post("/patient/auth/login", json={"login": "demo", "password": "secret"})
    assert response.status_code == 502
    assert response.json()["code"] == "http_error"
    assert response.json()["message"] == "Не удалось получить профиль пациента"


def test_me_allows_external_binding_without_cookie() -> None:
    client = TestClient(create_patient_api_app(container=_Container()))

    login = client.post(
        "/patient/auth/login",
        json={"login": "demo", "password": "secret"},
        headers={"X-External-Platform-User-Id": "max-user-1"},
    )
    assert login.status_code == 200
    client.cookies.clear()

    me = client.get("/patient/auth/me", headers={"X-External-Platform-User-Id": "max-user-1"})
    assert me.status_code == 200
    assert me.json()["patient_number"] == "p-1"


def test_unbind_external_user_resets_binding() -> None:
    client = TestClient(create_patient_api_app(container=_Container()))

    login = client.post(
        "/patient/auth/login",
        json={"login": "demo", "password": "secret"},
        headers={"X-External-Platform-User-Id": "max-user-2"},
    )
    assert login.status_code == 200

    unbind = client.post("/patient/auth/unbind", headers={"X-External-Platform-User-Id": "max-user-2"})
    assert unbind.status_code == 200

    client.cookies.clear()
    me = client.get("/patient/auth/me", headers={"X-External-Platform-User-Id": "max-user-2"})
    assert me.status_code == 401


def test_auto_login_token_one_time_flow() -> None:
    client = TestClient(create_patient_api_app(container=_Container()))

    save_login = client.post(
        "/bot/profile/save-login",
        json={"login": "demo"},
        headers={"X-Max-User-Id": "max-user-777"},
    )
    assert save_login.status_code == 200

    save_password = client.post(
        "/bot/profile/save-password",
        json={"password": "secret"},
        headers={"X-Max-User-Id": "max-user-777"},
    )
    assert save_password.status_code == 200

    token_response = client.post("/bot/miniapp-token/create", headers={"X-Max-User-Id": "max-user-777"})
    assert token_response.status_code == 200
    token = token_response.json()["auto_login_token"]

    redeem = client.post("/patient/auth/auto-login-token", json={"auto_login_token": token})
    assert redeem.status_code == 200
    assert redeem.json()["patient_number"] == "p-1"

    second_redeem = client.post("/patient/auth/auto-login-token", json={"auto_login_token": token})
    assert second_redeem.status_code == 401
