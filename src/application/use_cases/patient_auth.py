"""Use-cases для patient-facing auth/session flow."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.integration.errors import IntegrationErrorKind, IntegrationFailure
from src.integration.renovatio import RenovatioClient


@dataclass(frozen=True, slots=True)
class PatientSession:
    session_id: str
    patient_key: str
    patient_name: str
    patient_number: str
    created_at: datetime
    expires_at: datetime
    last_refresh_at: datetime
    auth_type: str
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class PatientSessionView:
    session_id: str
    patient_name: str
    patient_number: str
    created_at: datetime
    expires_at: datetime
    last_refresh_at: datetime
    auth_type: str


@dataclass(frozen=True, slots=True)
class PendingPhoneAuth:
    patient_id: str
    phone: str
    created_at: datetime


class PatientAuthError(ValueError):
    """Ошибка аутентификации пациента (невалидные credentials/code)."""


class PatientProfileFetchError(IntegrationFailure):
    """Ошибка получения patient profile после успешного auth."""

    def __init__(self, message: str) -> None:
        super().__init__(IntegrationErrorKind.BAD_RESPONSE, message)


class PatientSessionCreationError(RuntimeError):
    """Ошибка создания server-side session после auth/profile."""


class InMemoryPatientSessionRepositoryContract:
    def save(self, session: PatientSession) -> None: ...

    def get(self, session_id: str) -> PatientSession | None: ...

    def deactivate(self, session_id: str) -> None: ...


class PatientLoginUseCase:
    def __init__(self, client: RenovatioClient, session_repository: InMemoryPatientSessionRepositoryContract, *, session_ttl_minutes: int, key_lifetime_minutes: int) -> None:
        self._client = client
        self._session_repository = session_repository
        self._session_ttl_minutes = session_ttl_minutes
        self._key_lifetime_minutes = key_lifetime_minutes

    def execute(self, login: str, password: str) -> PatientSession:
        try:
            auth = self._client.auth_patient_by_login(login=login, password=password, lifetime=self._key_lifetime_minutes)
        except ValueError as exc:
            raise PatientAuthError(str(exc)) from exc
        patient_key = _extract_patient_key(auth_payload=auth)
        profile = _fetch_patient_profile(client=self._client, patient_key=patient_key)
        return _create_session(
            patient_key=patient_key,
            profile_payload=profile,
            auth_type="login",
            session_repository=self._session_repository,
            session_ttl_minutes=self._session_ttl_minutes,
        )


class PatientPhoneLoginUseCase:
    def __init__(self, client: RenovatioClient) -> None:
        self._client = client

    def execute(self, phone: str, *, key_lifetime_minutes: int) -> PendingPhoneAuth | PatientSession:
        auth = self._client.auth_patient_by_phone(phone=phone, lifetime=key_lifetime_minutes)
        if _truthy(auth.get("need_auth_key")):
            return PendingPhoneAuth(
                patient_id=str(auth.get("patient_id") or ""),
                phone=phone,
                created_at=datetime.now(timezone.utc),
            )
        raise PatientAuthError("Phone auth without code is not supported by current flow")


class ConfirmPatientAuthCodeUseCase:
    def __init__(self, client: RenovatioClient, session_repository: InMemoryPatientSessionRepositoryContract, *, session_ttl_minutes: int) -> None:
        self._client = client
        self._session_repository = session_repository
        self._session_ttl_minutes = session_ttl_minutes

    def execute(self, patient_id: str, code: str) -> PatientSession:
        try:
            auth = self._client.check_auth_code(patient_id=patient_id, code=code)
        except ValueError as exc:
            raise PatientAuthError(str(exc)) from exc
        patient_key = _extract_patient_key(auth_payload=auth)
        profile = _fetch_patient_profile(client=self._client, patient_key=patient_key)
        return _create_session(
            patient_key=patient_key,
            profile_payload=profile,
            auth_type="phone",
            session_repository=self._session_repository,
            session_ttl_minutes=self._session_ttl_minutes,
        )


class RefreshPatientSessionUseCase:
    def __init__(self, client: RenovatioClient, session_repository: InMemoryPatientSessionRepositoryContract, *, session_ttl_minutes: int, key_lifetime_minutes: int) -> None:
        self._client = client
        self._session_repository = session_repository
        self._session_ttl_minutes = session_ttl_minutes
        self._key_lifetime_minutes = key_lifetime_minutes

    def execute(self, session_id: str) -> PatientSession | None:
        session = self._session_repository.get(session_id)
        if session is None or not session.is_active or session.expires_at <= datetime.now(timezone.utc):
            return None

        refreshed = self._client.refresh_patient_key(session.patient_key, lifetime=self._key_lifetime_minutes)
        new_key = str(refreshed.get("patient_key") or session.patient_key)
        now = datetime.now(timezone.utc)
        updated = PatientSession(
            session_id=session.session_id,
            patient_key=new_key,
            patient_name=session.patient_name,
            patient_number=session.patient_number,
            created_at=session.created_at,
            expires_at=now + timedelta(minutes=self._session_ttl_minutes),
            last_refresh_at=now,
            auth_type=session.auth_type,
            is_active=True,
        )
        self._session_repository.save(updated)
        return updated


class GetCurrentPatientUseCase:
    def __init__(self, session_repository: InMemoryPatientSessionRepositoryContract) -> None:
        self._session_repository = session_repository

    def execute(self, session_id: str) -> PatientSession | None:
        session = self._session_repository.get(session_id)
        if session is None or not session.is_active:
            return None
        if session.expires_at <= datetime.now(timezone.utc):
            self._session_repository.deactivate(session_id)
            return None
        return session


def _extract_patient_key(*, auth_payload: dict) -> str:
    patient_key = str(auth_payload.get("patient_key") or "")
    if not patient_key:
        raise PatientAuthError("Renovatio auth response does not contain patient_key")
    return patient_key


def _fetch_patient_profile(*, client: RenovatioClient, patient_key: str) -> dict:
    try:
        fetch_by_key = getattr(client, "get_patient_info_by_key", None)
        if callable(fetch_by_key):
            return fetch_by_key(patient_key)
        return client.get_patient_info(patient_key)
    except IntegrationFailure as exc:
        raise PatientProfileFetchError(str(exc)) from exc


def _create_session(*, patient_key: str, profile_payload: dict, auth_type: str, session_repository: InMemoryPatientSessionRepositoryContract, session_ttl_minutes: int) -> PatientSession:
    now = datetime.now(timezone.utc)
    session = PatientSession(
        session_id=str(uuid4()),
        patient_key=patient_key,
        patient_name=str(profile_payload.get("patient_name") or profile_payload.get("full_name") or ""),
        patient_number=str(profile_payload.get("patient_number") or profile_payload.get("patient_id") or ""),
        created_at=now,
        expires_at=now + timedelta(minutes=session_ttl_minutes),
        last_refresh_at=now,
        auth_type=auth_type,
    )
    try:
        session_repository.save(session)
    except Exception as exc:  # noqa: BLE001 - explicitly mapped to semantic app error
        raise PatientSessionCreationError("Failed to create patient session") from exc
    return session


def _truthy(value: object) -> bool:
    return str(value).lower() in {"1", "true", "yes"}
