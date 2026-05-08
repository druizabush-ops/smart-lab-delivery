"""Patient auth/session endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response

from src.application.use_cases.patient_auth import (
    ConfirmPatientAuthCodeUseCase,
    PatientAuthError,
    PatientLoginUseCase,
    PatientPhoneLoginUseCase,
    PatientProfileFetchError,
    PatientSession,
    PatientSessionCreationError,
    PendingPhoneAuth,
)
from src.integration.errors import IntegrationFailure
from src.presentation.patient_api.schemas.auth import (
    LogoutResponse,
    ConfirmPatientCodeRequest,
    PatientLoginRequest,
    PatientPhoneLoginRequest,
    PatientSessionResponse,
    PhoneAuthPendingResponse,
)

router = APIRouter(prefix="/patient/auth", tags=["patient-auth"])


def _resolve_external_user_id(
    x_external_platform_user_id: Annotated[str | None, Header()] = None,
    x_max_user_id: Annotated[str | None, Header()] = None,
) -> str | None:
    """Возвращает внешний user_id в абстрактном формате без привязки к конкретному MAX-полю."""

    candidate = x_external_platform_user_id or x_max_user_id
    if candidate is None:
        return None
    normalized = candidate.strip()
    return normalized or None


@router.post("/login", response_model=PatientSessionResponse)
def login_by_credentials(
    request: PatientLoginRequest,
    http_response: Response,
    app_request: Request,
    external_platform_user_id: Annotated[str | None, Depends(_resolve_external_user_id)] = None,
) -> PatientSessionResponse:
    try:
        use_case: PatientLoginUseCase = app_request.app.state.patient_login_use_case
        session: PatientSession = use_case.execute(request.login, request.password)
    except PatientAuthError as exc:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль") from exc
    except PatientProfileFetchError as exc:
        raise HTTPException(status_code=502, detail="Не удалось получить профиль пациента") from exc
    except PatientSessionCreationError as exc:
        raise HTTPException(status_code=500, detail="Не удалось создать сессию пациента") from exc
    except IntegrationFailure as exc:
        raise HTTPException(status_code=502, detail="Ошибка интеграции авторизации пациента") from exc
    _set_session_cookie(http_response, session.session_id)
    if external_platform_user_id:
        app_request.app.state.bind_patient_session_use_case.execute(external_platform_user_id, session.session_id)
    return _session_response(session)


@router.post("/phone", response_model=PhoneAuthPendingResponse)
def login_by_phone(request: PatientPhoneLoginRequest, app_request: Request) -> PhoneAuthPendingResponse:
    try:
        use_case: PatientPhoneLoginUseCase = app_request.app.state.patient_phone_login_use_case
        response = use_case.execute(
            request.phone,
            key_lifetime_minutes=app_request.app.state.renovatio_settings.patient_key_lifetime_minutes,
        )
    except (PatientAuthError, ValueError, IntegrationFailure) as exc:
        raise HTTPException(status_code=401, detail="Не удалось инициировать вход по телефону") from exc
    if not isinstance(response, PendingPhoneAuth):
        raise HTTPException(status_code=500, detail="Неподдерживаемый ответ phone auth")
    return PhoneAuthPendingResponse(patient_id=response.patient_id, phone=response.phone, need_auth_key=True)


@router.post("/confirm-code", response_model=PatientSessionResponse)
def confirm_code(request: ConfirmPatientCodeRequest, http_response: Response, app_request: Request) -> PatientSessionResponse:
    try:
        use_case: ConfirmPatientAuthCodeUseCase = app_request.app.state.confirm_patient_auth_code_use_case
        session: PatientSession = use_case.execute(request.patient_id, request.code)
    except PatientAuthError as exc:
        raise HTTPException(status_code=401, detail="Неверный SMS код") from exc
    except PatientProfileFetchError as exc:
        raise HTTPException(status_code=502, detail="Не удалось получить профиль пациента") from exc
    except PatientSessionCreationError as exc:
        raise HTTPException(status_code=500, detail="Не удалось создать сессию пациента") from exc
    except IntegrationFailure as exc:
        raise HTTPException(status_code=502, detail="Ошибка интеграции подтверждения кода") from exc
    _set_session_cookie(http_response, session.session_id)
    return _session_response(session)


@router.post("/refresh", response_model=PatientSessionResponse)
def refresh_session(request: Request) -> PatientSessionResponse:
    session_id = request.cookies.get("sld_patient_session")
    if not session_id:
        raise HTTPException(status_code=401, detail="Нет активной сессии")
    refreshed = request.app.state.refresh_patient_session_use_case.execute(session_id)
    if refreshed is None:
        raise HTTPException(status_code=401, detail="Сессия недействительна")
    return _session_response(refreshed)


@router.post("/logout", response_model=LogoutResponse)
def logout(response: Response, request: Request) -> LogoutResponse:
    session_id = request.cookies.get("sld_patient_session")
    if session_id:
        request.app.state.patient_session_repository.deactivate(session_id)
    response.delete_cookie("sld_patient_session")
    return LogoutResponse(success=True)


@router.post("/unbind", response_model=LogoutResponse)
def unbind_external_user(
    request: Request,
    external_platform_user_id: Annotated[str | None, Depends(_resolve_external_user_id)] = None,
) -> LogoutResponse:
    if not external_platform_user_id:
        raise HTTPException(status_code=400, detail="Не передан внешний идентификатор пользователя")
    request.app.state.unbind_patient_session_use_case.execute(external_platform_user_id)
    return LogoutResponse(success=True)


@router.get("/me", response_model=PatientSessionResponse)
def get_me(
    request: Request,
    response: Response,
    external_platform_user_id: Annotated[str | None, Depends(_resolve_external_user_id)] = None,
) -> PatientSessionResponse:
    session_id = request.cookies.get("sld_patient_session")
    if not session_id and external_platform_user_id:
        session_id = request.app.state.resolve_bound_patient_session_use_case.execute(external_platform_user_id)
        if session_id:
            _set_session_cookie(response, session_id)
    if not session_id:
        raise HTTPException(status_code=401, detail="Нет активной сессии")
    session = request.app.state.get_current_patient_use_case.execute(session_id)
    if session is None:
        raise HTTPException(status_code=401, detail="Сессия недействительна")
    return _session_response(session)


@router.post("/auto-login-token", response_model=PatientSessionResponse)
def auto_login_by_token(request: Request, http_response: Response, token_payload: dict[str, str]) -> PatientSessionResponse:
    token = token_payload.get("auto_login_token", "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="Токен не передан")
    max_user_id = request.app.state.bot_miniapp_token_use_case.redeem(token)
    if not max_user_id:
        raise HTTPException(status_code=401, detail="Токен недействителен")
    try:
        login, password = request.app.state.bot_profile_use_case.get_credentials(max_user_id)
        session: PatientSession = request.app.state.patient_login_use_case.execute(login, password)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Не удалось выполнить вход") from exc
    _set_session_cookie(http_response, session.session_id)
    return _session_response(session)


def _set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key="sld_patient_session",
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )


def _session_response(session: PatientSession) -> PatientSessionResponse:
    return PatientSessionResponse(
        session_id=session.session_id,
        patient_name=session.patient_name,
        patient_number=session.patient_number,
        created_at=session.created_at,
        expires_at=session.expires_at,
        last_refresh_at=session.last_refresh_at,
        auth_type=session.auth_type,
    )
