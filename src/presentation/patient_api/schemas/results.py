"""Pydantic-схемы patient-facing read API."""

from datetime import datetime

from pydantic import BaseModel


class PatientResultDocumentResponse(BaseModel):
    title: str
    url: str | None
    readiness: str


class PatientResultResponse(BaseModel):
    result_id: str
    patient_id: str
    status: str
    channel: str
    created_at: datetime
    updated_at: datetime
    attempts_count: int
    last_error: str | None
    documents: list[PatientResultDocumentResponse]
