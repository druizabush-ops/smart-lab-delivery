"""Use-case слой patient-facing результатов через Renovatio + server-side session."""

import base64
import binascii
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.application.use_cases.patient_auth import GetCurrentPatientUseCase, PatientSession
from src.integration.errors import IntegrationErrorKind, IntegrationFailure
from src.integration.renovatio import RenovatioClient


class PatientResultsAccessError(RuntimeError):
    """Сигнализирует об отсутствии или невалидности patient session."""


class PatientLabResultNotFoundError(RuntimeError):
    """Сигнализирует, что запрошенный результат отсутствует в источнике."""


class PatientResultPdfNotAvailableError(RuntimeError):
    """Сигнализирует, что у результата отсутствует PDF документ."""


class PatientResultPdfPayloadError(RuntimeError):
    """Сигнализирует о невалидном payload PDF от интеграции."""


@dataclass(frozen=True, slots=True)
class PatientLabResultDocumentDto:
    document_id: str
    title: str
    url: str | None
    readiness: str
    mime_type: str | None


@dataclass(frozen=True, slots=True)
class PatientLabResultListItemDto:
    result_id: str
    date: str | None
    datetime: datetime | None
    lab_id: str | None
    lab: str | None
    clinic_id: str | None
    clinic: str | None
    services: list[str]
    files_count: int


@dataclass(frozen=True, slots=True)
class PatientLabResultDetailsDto:
    result_id: str
    date: str | None
    datetime: datetime | None
    lab_id: str | None
    lab: str | None
    clinic_id: str | None
    clinic: str | None
    services: list[str]
    sections: list[dict[str, Any]]
    indicators: list[dict[str, Any]]
    documents: list[PatientLabResultDocumentDto]


@dataclass(frozen=True, slots=True)
class PatientResultPdfDto:
    """DTO бинарного PDF-документа результата."""

    result_id: str
    filename: str
    mime_type: str
    content: bytes


class PatientResultsUseCase:
    """Единый application-слой для patient-facing результатов."""

    def __init__(self, *, sessions: GetCurrentPatientUseCase, renovatio_client: RenovatioClient) -> None:
        self._sessions = sessions
        self._renovatio_client = renovatio_client

    def list_results_by_session(
        self,
        *,
        session_id: str,
        lab_id: str | None = None,
        clinic_id: str | None = None,
    ) -> list[PatientLabResultListItemDto]:
        session = self._get_active_session(session_id)
        payload = self._renovatio_client.get_patient_lab_results_by_key(
            session.patient_key,
            lab_id=lab_id,
            clinic_id=clinic_id,
        )
        return [_map_result_list_item(item) for item in payload]

    def get_result_details_by_session(
        self,
        *,
        session_id: str,
        result_id: str,
        lab_id: str | None = None,
        clinic_id: str | None = None,
    ) -> PatientLabResultDetailsDto:
        session = self._get_active_session(session_id)
        try:
            payload = self._renovatio_client.get_patient_lab_result_details_by_key(
                session.patient_key,
                result_id,
                lab_id=lab_id,
                clinic_id=clinic_id,
            )
        except IntegrationFailure as exc:
            if exc.kind is IntegrationErrorKind.EMPTY_RESULT:
                raise PatientLabResultNotFoundError(result_id) from exc
            raise

        if not payload:
            raise PatientLabResultNotFoundError(result_id)
        return _map_result_details(payload)

    def _get_active_session(self, session_id: str) -> PatientSession:
        session = self._sessions.execute(session_id)
        now = datetime.now(timezone.utc)
        if session is None or not session.is_active or session.expires_at <= now:
            raise PatientResultsAccessError("Patient session недействительна или отсутствует")
        return session


class PatientResultPdfUseCase:
    """Сценарий получения PDF результата через patient session и Renovatio details."""

    def __init__(self, *, sessions: GetCurrentPatientUseCase, renovatio_client: RenovatioClient) -> None:
        self._sessions = sessions
        self._renovatio_client = renovatio_client

    def get_pdf_by_session(
        self,
        *,
        session_id: str,
        result_id: str,
        lab_id: str | None = None,
        clinic_id: str | None = None,
    ) -> PatientResultPdfDto:
        session = self._get_active_session(session_id)
        try:
            payload = self._renovatio_client.get_patient_lab_result_details_by_key(
                session.patient_key,
                result_id,
                lab_id=lab_id,
                clinic_id=clinic_id,
            )
        except IntegrationFailure as exc:
            if exc.kind is IntegrationErrorKind.EMPTY_RESULT:
                raise PatientLabResultNotFoundError(result_id) from exc
            raise

        if not payload:
            raise PatientLabResultNotFoundError(result_id)

        files = payload.get("files")
        if not isinstance(files, list) or not files:
            raise PatientResultPdfNotAvailableError("В details payload отсутствует data.files")

        first_file = files[0]
        if not isinstance(first_file, str) or not first_file.strip():
            raise PatientResultPdfPayloadError("Первый элемент data.files не содержит base64 PDF")

        try:
            decoded = base64.b64decode(first_file, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise PatientResultPdfPayloadError("Не удалось декодировать PDF из base64") from exc

        if not decoded.startswith(b"%PDF"):
            raise PatientResultPdfPayloadError("Декодированный файл не похож на PDF")

        return PatientResultPdfDto(
            result_id=result_id,
            filename=_build_pdf_filename(result_id),
            mime_type="application/pdf",
            content=decoded,
        )

    def _get_active_session(self, session_id: str) -> PatientSession:
        session = self._sessions.execute(session_id)
        now = datetime.now(timezone.utc)
        if session is None or not session.is_active or session.expires_at <= now:
            raise PatientResultsAccessError("Patient session недействительна или отсутствует")
        return session


def _map_result_list_item(raw: dict[str, Any]) -> PatientLabResultListItemDto:
    documents = _extract_documents(raw)
    return PatientLabResultListItemDto(
        result_id=_first_str(raw, "result_id", "id", "lab_result_id"),
        date=_first_optional_str(raw, "date"),
        datetime=_parse_datetime(_first_optional_str(raw, "datetime", "date_time", "created_at")),
        lab_id=_first_optional_str(raw, "lab_id"),
        lab=_first_optional_str(raw, "lab", "lab_name"),
        clinic_id=_first_optional_str(raw, "clinic_id"),
        clinic=_first_optional_str(raw, "clinic", "clinic_name"),
        services=_extract_services(raw),
        files_count=len(documents),
    )


def _map_result_details(raw: dict[str, Any]) -> PatientLabResultDetailsDto:
    documents = _extract_documents(raw)
    return PatientLabResultDetailsDto(
        result_id=_first_str(raw, "result_id", "id", "lab_result_id"),
        date=_first_optional_str(raw, "date"),
        datetime=_parse_datetime(_first_optional_str(raw, "datetime", "date_time", "created_at")),
        lab_id=_first_optional_str(raw, "lab_id"),
        lab=_first_optional_str(raw, "lab", "lab_name"),
        clinic_id=_first_optional_str(raw, "clinic_id"),
        clinic=_first_optional_str(raw, "clinic", "clinic_name"),
        services=_extract_services(raw),
        sections=_extract_list(raw, "sections", "result_sections"),
        indicators=_extract_list(raw, "indicators", "result_indicators", "results"),
        documents=documents,
    )


def _extract_documents(raw: dict[str, Any]) -> list[PatientLabResultDocumentDto]:
    values = _extract_list(raw, "documents", "files", "pdfs")
    documents: list[PatientLabResultDocumentDto] = []
    for item in values:
        if not isinstance(item, dict):
            continue
        url = _first_optional_str(item, "url", "file_url", "pdf_url", "link")
        documents.append(
            PatientLabResultDocumentDto(
                document_id=_first_str(item, "document_id", "id", default=f"doc-{len(documents)+1}"),
                title=_first_str(item, "title", "name", default="Документ результата"),
                url=url,
                readiness="ready" if url else "pending",
                mime_type=_first_optional_str(item, "mime_type", "content_type"),
            )
        )
    return documents


def _build_pdf_filename(result_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in result_id).strip("-")
    return f"result-{safe or 'unknown'}.pdf"


def _extract_services(raw: dict[str, Any]) -> list[str]:
    services = raw.get("services")
    if isinstance(services, list):
        normalized: list[str] = []
        for item in services:
            if isinstance(item, str) and item.strip():
                normalized.append(item.strip())
            elif isinstance(item, dict):
                title = _first_optional_str(item, "title", "name", "service")
                if title:
                    normalized.append(title)
        return normalized
    return []


def _extract_list(raw: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _first_str(raw: dict[str, Any], *keys: str, default: str = "") -> str:
    value = _first_optional_str(raw, *keys)
    if value:
        return value
    return default


def _first_optional_str(raw: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = raw.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None
