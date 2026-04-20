"""Patient auth/session endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from src.application.use_cases.patient_auth import PendingPhoneAuth, PatientSession
from src.integration.errors import IntegrationFailure
from src.presentation.patient_api.schemas.auth import (
    ConfirmPatientCodeRequest,
    LogoutResponse,
    PatientLoginRequest,
    PatientPhoneLoginRequest,
    PatientSessionResponse,
    PhoneAuthPendingResponse,
)

router = APIRouter(prefix="/patient/auth", tags=["patient-auth"])


@router.post("/login", response_model=PatientSessionResponse)
def login_by_credentials(request: PatientLoginRequest, http_response: Response, app_request: Request) -> PatientSessionResponse:
    try:
        session: PatientSession = app_request.app.state.patient_login_use_case.execute(request.login, request.password)
    except (ValueError, IntegrationFailure) as exc:
        raise HTTPException(status_code=401, detail="Неверные учетные данные") from exc
    _set_session_cookie(http_response, session.session_id)
    return _session_response(session)


@router.post("/phone", response_model=PhoneAuthPendingResponse)
def login_by_phone(request: PatientPhoneLoginRequest, app_request: Request) -> PhoneAuthPendingResponse:
    try:
        response = app_request.app.state.patient_phone_login_use_case.execute(
            request.phone,
            key_lifetime_minutes=app_request.app.state.renovatio_settings.patient_key_lifetime_minutes,
        )
    except (ValueError, IntegrationFailure) as exc:
        raise HTTPException(status_code=401, detail="Не удалось инициировать вход по телефону") from exc
    if not isinstance(response, PendingPhoneAuth):
        raise HTTPException(status_code=500, detail="Неподдерживаемый ответ phone auth")
    return PhoneAuthPendingResponse(patient_id=response.patient_id, phone=response.phone, need_auth_key=True)


@router.post("/confirm-code", response_model=PatientSessionResponse)
def confirm_code(request: ConfirmPatientCodeRequest, http_response: Response, app_request: Request) -> PatientSessionResponse:
    try:
        session: PatientSession = app_request.app.state.confirm_patient_auth_code_use_case.execute(request.patient_id, request.code)
    except (ValueError, IntegrationFailure) as exc:
        raise HTTPException(status_code=401, detail="Неверный SMS код") from exc
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


@router.get("/me", response_model=PatientSessionResponse)
def get_me(request: Request) -> PatientSessionResponse:
    session_id = request.cookies.get("sld_patient_session")
    if not session_id:
        raise HTTPException(status_code=401, detail="Нет активной сессии")
    session = request.app.state.get_current_patient_use_case.execute(session_id)
    if session is None:
        raise HTTPException(status_code=401, detail="Сессия недействительна")
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
