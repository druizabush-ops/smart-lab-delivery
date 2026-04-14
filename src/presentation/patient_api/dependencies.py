"""DI-зависимости patient API."""

from fastapi import Request

from src.application.services import PatientResultReadService


def get_patient_read_service(request: Request) -> PatientResultReadService:
    return request.app.state.patient_result_read_service
