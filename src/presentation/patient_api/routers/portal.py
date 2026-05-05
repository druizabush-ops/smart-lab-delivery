from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.application.use_cases.patient_portal_data import PatientPortalDataUseCase
from src.presentation.patient_api.dependencies import get_patient_portal_use_case, get_patient_session_id
from src.presentation.patient_api.schemas.portal import (
    AppointmentSlotResponse,
    PatientBalanceResponse,
    ServiceCategoryResponse,
    ServiceResponse,
)

router = APIRouter(prefix="/patient", tags=["patient-portal"])


@router.get("/loyalty", response_model=PatientBalanceResponse)
def get_loyalty(
    session_id: Annotated[str, Depends(get_patient_session_id)],
    use_case: Annotated[PatientPortalDataUseCase, Depends(get_patient_portal_use_case)],
) -> PatientBalanceResponse:
    return PatientBalanceResponse.model_validate(use_case.get_balance(session_id), from_attributes=True)


@router.get("/services/categories", response_model=list[ServiceCategoryResponse])
def get_service_categories(
    use_case: Annotated[PatientPortalDataUseCase, Depends(get_patient_portal_use_case)],
) -> list[ServiceCategoryResponse]:
    return [ServiceCategoryResponse.model_validate(item, from_attributes=True) for item in use_case.get_services_categories()]


@router.get("/services", response_model=list[ServiceResponse])
def get_services(
    category_id: str | None = Query(default=None),
    use_case: Annotated[PatientPortalDataUseCase, Depends(get_patient_portal_use_case)] = None,
) -> list[ServiceResponse]:
    return [ServiceResponse.model_validate(item, from_attributes=True) for item in use_case.get_services(category_id=category_id)]


@router.get("/services/search", response_model=list[ServiceResponse])
def search_services(
    q: str = Query(default=""),
    category_id: str | None = Query(default=None),
    use_case: Annotated[PatientPortalDataUseCase, Depends(get_patient_portal_use_case)] = None,
) -> list[ServiceResponse]:
    return [ServiceResponse.model_validate(item, from_attributes=True) for item in use_case.search_services(q=q, category_id=category_id)]


@router.get("/appointments/schedule", response_model=list[AppointmentSlotResponse])
def get_appointments_schedule(
    session_id: Annotated[str, Depends(get_patient_session_id)] = "",
    use_case: Annotated[PatientPortalDataUseCase, Depends(get_patient_portal_use_case)] = None,
) -> list[AppointmentSlotResponse]:
    return [AppointmentSlotResponse.model_validate(item, from_attributes=True) for item in use_case.get_schedule(session_id=session_id)]
