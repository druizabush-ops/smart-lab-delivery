"""DI-зависимости patient API."""

from fastapi import HTTPException, Request

from src.application.use_cases.patient_results import PatientResultsUseCase


def get_patient_session_id(request: Request) -> str:
    """Возвращает session_id из cookie как единственный trust-source контекста пациента."""

    session_id = request.cookies.get("sld_patient_session")
    if not session_id:
        raise HTTPException(status_code=401, detail="Не найдена активная patient session")
    return session_id


def get_patient_results_use_case(request: Request) -> PatientResultsUseCase:
    return request.app.state.patient_results_use_case
