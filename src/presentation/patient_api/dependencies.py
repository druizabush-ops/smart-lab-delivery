"""DI-зависимости patient API."""

from fastapi import HTTPException, Request

from src.application.use_cases.patient_results import PatientResultPdfUseCase, PatientResultsUseCase
from src.application.use_cases.patient_portal_data import PatientPortalDataUseCase


def get_patient_session_id(request: Request) -> str:
    """Возвращает session_id из cookie как единственный trust-source контекста пациента."""

    session_id = request.cookies.get("sld_patient_session")
    if not session_id:
        raise HTTPException(status_code=401, detail="Не найдена активная patient session")
    return session_id


def get_patient_results_use_case(request: Request) -> PatientResultsUseCase:
    return request.app.state.patient_results_use_case


def get_patient_result_pdf_use_case(request: Request) -> PatientResultPdfUseCase:
    return request.app.state.patient_result_pdf_use_case


def get_patient_portal_use_case(request: Request) -> PatientPortalDataUseCase:
    return request.app.state.patient_portal_use_case
