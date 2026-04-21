"""Patient-facing endpoints для результатов через session + Renovatio."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.use_cases.patient_results import (
    PatientLabResultNotFoundError,
    PatientResultsAccessError,
    PatientResultsUseCase,
)
from src.presentation.patient_api.dependencies import (
    get_patient_results_use_case,
    get_patient_session_id,
)
from src.presentation.patient_api.schemas import (
    PatientLabResultDetailsResponse,
    PatientLabResultListItemResponse,
)

router = APIRouter(prefix="/patient/results", tags=["patient-results"])


@router.get("", response_model=list[PatientLabResultListItemResponse])
def list_results(
    _: str | None = Query(default=None, alias="patient_id"),
    __: str | None = Query(default=None, alias="start_param"),
    lab_id: str | None = Query(default=None),
    clinic_id: str | None = Query(default=None),
    session_id: Annotated[str, Depends(get_patient_session_id)] = "",
    use_case: Annotated[PatientResultsUseCase, Depends(get_patient_results_use_case)] = None,
) -> list[PatientLabResultListItemResponse]:
    try:
        results = use_case.list_results_by_session(session_id=session_id, lab_id=lab_id, clinic_id=clinic_id)
    except PatientResultsAccessError as exc:
        raise HTTPException(status_code=401, detail="Patient session недействительна или истекла") from exc
    return [PatientLabResultListItemResponse.model_validate(item, from_attributes=True) for item in results]


@router.get("/{result_id}", response_model=PatientLabResultDetailsResponse)
def get_result(
    result_id: str,
    _: str | None = Query(default=None, alias="patient_id"),
    __: str | None = Query(default=None, alias="start_param"),
    lab_id: str | None = Query(default=None),
    clinic_id: str | None = Query(default=None),
    session_id: Annotated[str, Depends(get_patient_session_id)] = "",
    use_case: Annotated[PatientResultsUseCase, Depends(get_patient_results_use_case)] = None,
) -> PatientLabResultDetailsResponse:
    try:
        result = use_case.get_result_details_by_session(
            session_id=session_id,
            result_id=result_id,
            lab_id=lab_id,
            clinic_id=clinic_id,
        )
    except PatientResultsAccessError as exc:
        raise HTTPException(status_code=401, detail="Patient session недействительна или истекла") from exc
    except PatientLabResultNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Результат не найден")
    return PatientLabResultDetailsResponse.model_validate(result, from_attributes=True)
