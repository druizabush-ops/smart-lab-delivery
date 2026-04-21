"""Pydantic-схемы patient-facing results API."""

from datetime import datetime

from pydantic import BaseModel


class PatientLabResultDocumentResponse(BaseModel):
    document_id: str
    title: str
    url: str | None
    readiness: str
    mime_type: str | None = None


class PatientLabResultListItemResponse(BaseModel):
    result_id: str
    date: str | None
    datetime: datetime | None
    lab_id: str | None
    lab: str | None
    clinic_id: str | None
    clinic: str | None
    services: list[str]
    files_count: int


class PatientLabResultDetailsResponse(BaseModel):
    result_id: str
    date: str | None
    datetime: datetime | None
    lab_id: str | None
    lab: str | None
    clinic_id: str | None
    clinic: str | None
    services: list[str]
    sections: list[dict]
    indicators: list[dict]
    documents: list[PatientLabResultDocumentResponse]
