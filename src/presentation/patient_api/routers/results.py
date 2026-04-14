"""Patient-facing read-only endpoints mini app."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.services import PatientResultReadService
from src.presentation.patient_api.dependencies import get_patient_read_service
from src.presentation.patient_api.schemas import PatientResultResponse

router = APIRouter(prefix="/patient/results", tags=["patient-results"])


@router.get("", response_model=list[PatientResultResponse])
def list_results(
    patient_id: str = Query(...),
    read_service: Annotated[PatientResultReadService, Depends(get_patient_read_service)] = None,
) -> list[PatientResultResponse]:
    results = read_service.list_results(patient_id=patient_id)
    return [PatientResultResponse.model_validate(item, from_attributes=True) for item in results]


@router.get("/{result_id}", response_model=PatientResultResponse)
def get_result(
    result_id: str,
    patient_id: str = Query(...),
    read_service: Annotated[PatientResultReadService, Depends(get_patient_read_service)] = None,
) -> PatientResultResponse:
    result = read_service.get_result(patient_id=patient_id, result_id=result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Результат не найден")
    return PatientResultResponse.model_validate(result, from_attributes=True)
