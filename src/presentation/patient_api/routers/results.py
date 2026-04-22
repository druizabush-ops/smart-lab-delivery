"""Patient-facing endpoints для результатов через session + Renovatio."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from src.application.use_cases.patient_results import (
    PatientLabResultNotFoundError,
    PatientResultPdfNotAvailableError,
    PatientResultPdfPayloadError,
    PatientResultPdfUseCase,
    PatientResultsAccessError,
    PatientResultsUseCase,
)
from src.presentation.patient_api.dependencies import (
    get_patient_result_pdf_use_case,
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


@router.get("/{result_id}/pdf")
def download_result_pdf(
    result_id: str,
    _: str | None = Query(default=None, alias="patient_id"),
    __: str | None = Query(default=None, alias="start_param"),
    lab_id: str | None = Query(default=None),
    clinic_id: str | None = Query(default=None),
    disposition: str = Query(default="attachment", pattern="^(inline|attachment)$"),
    session_id: Annotated[str, Depends(get_patient_session_id)] = "",
    use_case: Annotated[PatientResultPdfUseCase, Depends(get_patient_result_pdf_use_case)] = None,
) -> Response:
    try:
        pdf = use_case.get_pdf_by_session(
            session_id=session_id,
            result_id=result_id,
            lab_id=lab_id,
            clinic_id=clinic_id,
        )
    except PatientResultsAccessError as exc:
        raise HTTPException(status_code=401, detail="Patient session недействительна или истекла") from exc
    except PatientLabResultNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Результат не найден") from exc
    except PatientResultPdfNotAvailableError as exc:
        raise HTTPException(status_code=404, detail="PDF файл результата отсутствует") from exc
    except PatientResultPdfPayloadError as exc:
        raise HTTPException(status_code=502, detail="Интеграция вернула невалидный PDF payload") from exc

    return Response(
        content=pdf.content,
        media_type=pdf.mime_type,
        headers={"Content-Disposition": f'{disposition}; filename="{pdf.filename}"'},
    )
