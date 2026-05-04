from datetime import datetime, timezone

import pytest

from src.application.use_cases.patient_auth import (
    ConfirmPatientAuthCodeUseCase,
    PatientAuthError,
    PatientLoginUseCase,
    PatientProfileFetchError,
    PatientSession,
    PatientSessionCreationError,
)
from src.integration.errors import IntegrationErrorKind, IntegrationFailure


class _SessionRepo:
    def __init__(self) -> None:
        self.saved: dict[str, PatientSession] = {}

    def save(self, session: PatientSession) -> None:
        self.saved[session.session_id] = session

    def get(self, session_id: str) -> PatientSession | None:
        return self.saved.get(session_id)

    def deactivate(self, session_id: str) -> None:
        if session_id in self.saved:
            current = self.saved[session_id]
            self.saved[session_id] = PatientSession(
                session_id=current.session_id,
                patient_key=current.patient_key,
                patient_name=current.patient_name,
                patient_number=current.patient_number,
                created_at=current.created_at,
                expires_at=current.expires_at,
                last_refresh_at=datetime.now(timezone.utc),
                auth_type=current.auth_type,
                birth_date=current.birth_date,
                phone=current.phone,
                email=current.email,
                avatar_url=current.avatar_url,
                is_active=False,
            )


class _BrokenSessionRepo(_SessionRepo):
    def save(self, session: PatientSession) -> None:
        raise RuntimeError("disk failure")


class _RenovatioClientStub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def auth_patient_by_login(self, login: str, password: str, lifetime=None):
        if login != "demo" or password != "secret":
            raise ValueError("bad creds")
        self.calls.append(("auth_login", login))
        return {"patient_key": "pk-1", "patient_id": None, "need_auth_key": 0}

    def get_patient_info(self, patient_key: str):
        self.calls.append(("get_patient_info", patient_key))
        if patient_key == "pk-bad-profile":
            raise IntegrationFailure(IntegrationErrorKind.BAD_RESPONSE, "bad profile")
        return {
            "number": "P-100",
            "last_name": "Иванов",
            "first_name": "Иван",
            "third_name": "Иванович",
            "birth_date": "15.05.1985",
            "phone": "+7 (999) 123-45-67",
            "email": "ivanov@example.ru",
            "patient_id": "internal-id",
        }

    def check_auth_code(self, patient_id: str, code: str):
        if code != "1234":
            raise ValueError("bad code")
        self.calls.append(("check_auth_code", patient_id))
        return {"patient_key": "pk-2", "patient_id": patient_id}


def test_login_fetches_profile_and_creates_session_from_get_patient_info() -> None:
    client = _RenovatioClientStub()
    repo = _SessionRepo()
    use_case = PatientLoginUseCase(client, repo, session_ttl_minutes=120, key_lifetime_minutes=120)

    session = use_case.execute("demo", "secret")

    assert session.patient_key == "pk-1"
    assert session.patient_name == "Иванов Иван Иванович"
    assert session.patient_number == "P-100"
    assert session.birth_date == "15.05.1985"
    assert session.phone == "+7 (999) 123-45-67"
    assert session.email == "ivanov@example.ru"
    assert ("auth_login", "demo") in client.calls
    assert ("get_patient_info", "pk-1") in client.calls


def test_login_does_not_fail_when_auth_patient_id_is_null() -> None:
    client = _RenovatioClientStub()
    repo = _SessionRepo()
    use_case = PatientLoginUseCase(client, repo, session_ttl_minutes=120, key_lifetime_minutes=120)

    session = use_case.execute("demo", "secret")

    assert session.patient_number == "P-100"


def test_login_uses_full_name_when_present() -> None:
    class _FullNameClient(_RenovatioClientStub):
        def get_patient_info(self, patient_key: str):
            return {"full_name": "Готовое Имя", "number": "P-200", "last_name": "Иванов", "first_name": "Иван"}

    client = _FullNameClient()
    repo = _SessionRepo()
    use_case = PatientLoginUseCase(client, repo, session_ttl_minutes=120, key_lifetime_minutes=120)

    session = use_case.execute("demo", "secret")

    assert session.patient_name == "Готовое Имя"
    assert session.patient_number == "P-200"


def test_login_raises_profile_error_when_profile_fetch_failed() -> None:
    class _BrokenProfileClient(_RenovatioClientStub):
        def auth_patient_by_login(self, login: str, password: str, lifetime=None):
            return {"patient_key": "pk-bad-profile", "patient_id": None}

    client = _BrokenProfileClient()
    repo = _SessionRepo()
    use_case = PatientLoginUseCase(client, repo, session_ttl_minutes=120, key_lifetime_minutes=120)

    with pytest.raises(PatientProfileFetchError):
        use_case.execute("demo", "secret")


def test_confirm_code_flow_fetches_profile_before_session_create() -> None:
    client = _RenovatioClientStub()
    repo = _SessionRepo()
    use_case = ConfirmPatientAuthCodeUseCase(client, repo, session_ttl_minutes=120)

    session = use_case.execute(patient_id="p-1", code="1234")

    assert session.auth_type == "phone"
    assert ("check_auth_code", "p-1") in client.calls
    assert ("get_patient_info", "pk-2") in client.calls


def test_session_creation_failure_is_mapped_to_semantic_error() -> None:
    client = _RenovatioClientStub()
    repo = _BrokenSessionRepo()
    use_case = PatientLoginUseCase(client, repo, session_ttl_minutes=120, key_lifetime_minutes=120)

    with pytest.raises(PatientSessionCreationError):
        use_case.execute("demo", "secret")


def test_login_bad_credentials_raise_auth_error() -> None:
    client = _RenovatioClientStub()
    repo = _SessionRepo()
    use_case = PatientLoginUseCase(client, repo, session_ttl_minutes=120, key_lifetime_minutes=120)

    with pytest.raises(PatientAuthError):
        use_case.execute("demo", "wrong")
