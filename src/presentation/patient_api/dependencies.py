"""DI-зависимости patient API."""

from dataclasses import dataclass

from fastapi import HTTPException, Request

from src.application.security import validate_max_webapp_data
from src.application.services import PatientResultReadService
from src.config.security_settings import SecuritySettings


@dataclass(frozen=True, slots=True)
class PatientAccessContext:
    """Контекст безопасного определения patient_id для patient API."""

    patient_id: str
    source: str


def get_patient_read_service(request: Request) -> PatientResultReadService:
    return request.app.state.patient_result_read_service


def get_patient_access_context(request: Request) -> PatientAccessContext:
    """Определяет доверенный patient_id из серверно-проверенного init_data."""

    settings: SecuritySettings = request.app.state.security_settings
    query_patient_id = request.query_params.get("patient_id")
    query_start_param = request.query_params.get("start_param")
    init_data = request.headers.get("X-Max-Init-Data", "")

    if init_data:
        validation = validate_max_webapp_data(init_data=init_data, secret=settings.max_webapp_secret)
        if not validation.is_valid:
            raise HTTPException(status_code=401, detail=f"Недоверенный MAX context: {validation.reason}")
        if query_start_param and validation.start_param and query_start_param != validation.start_param:
            raise HTTPException(status_code=401, detail="start_param не совпадает с подписанным init_data")
        if not validation.user_id:
            raise HTTPException(status_code=401, detail="В init_data отсутствует user.id")
        return PatientAccessContext(patient_id=validation.user_id, source="max_init_data")

    if settings.patient_security_mode == "relaxed" and query_patient_id:
        return PatientAccessContext(patient_id=query_patient_id, source="query_fallback")

    raise HTTPException(status_code=401, detail="Не предоставлен доверенный пациентский контекст")
