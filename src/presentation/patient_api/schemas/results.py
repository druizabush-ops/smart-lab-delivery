"""Pydantic-схемы patient-facing results API."""

from pydantic import BaseModel


class PatientLabResultListItemResponse(BaseModel):
    result_id: str
    title: str
    date: str | None
    status: str
    has_pdf: bool
    lab_name: str | None
    clinic_name: str | None
    short_services_summary: str | None


class PatientLabResultDetailsResponse(BaseModel):
    result_id: str
    title: str
    date: str | None
    status: str
    has_pdf: bool
    lab_name: str | None
    clinic_name: str | None
    services: list[str]
    sections: list[dict]
    indicators: list[dict]
    pdf_open_url: str | None
    pdf_download_url: str | None
