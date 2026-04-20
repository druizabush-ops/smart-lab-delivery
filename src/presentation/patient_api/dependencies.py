"""DI-зависимости patient API."""

from dataclasses import dataclass

from fastapi import HTTPException, Request

from src.application.services import PatientResultReadService
from src.application.use_cases.patient_auth import GetCurrentPatientUseCase, PatientSession


@dataclass(frozen=True, slots=True)
class PatientAccessContext:
    """Контекст авторизованного patient API пользователя."""

    patient_id: str
    source: str


def get_current_patient_use_case(request: Request) -> GetCurrentPatientUseCase:
    return request.app.state.get_current_patient_use_case


def get_current_patient_session(
    request: Request,
    get_current_patient: GetCurrentPatientUseCase,
) -> PatientSession:
    session_id = request.cookies.get("sld_patient_session")
    if not session_id:
        raise HTTPException(status_code=401, detail="Не найдена активная patient session")
    session = get_current_patient.execute(session_id)
    if session is None:
        raise HTTPException(status_code=401, detail="Patient session недействительна или истекла")
    return session


def get_patient_read_service(request: Request) -> PatientResultReadService:
    return request.app.state.patient_result_read_service


def get_patient_access_context(request: Request) -> PatientAccessContext:
    """Определяет доверенный patient_id из server-side session."""

    get_current_patient: GetCurrentPatientUseCase | None = getattr(request.app.state, "get_current_patient_use_case", None)
    if get_current_patient is None:
        query_patient_id = request.query_params.get("patient_id")
        if query_patient_id:
            return PatientAccessContext(patient_id=query_patient_id, source="legacy_query_fallback")
        raise HTTPException(status_code=401, detail="Не найдена active patient session")

    session_id = request.cookies.get("sld_patient_session")
    if not session_id:
        raise HTTPException(status_code=401, detail="Не найдена активная patient session")
    session = get_current_patient.execute(session_id)
    if session is None:
        raise HTTPException(status_code=401, detail="Patient session недействительна или истекла")
    return PatientAccessContext(patient_id=session.patient_number, source="server_session")
