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
class PatientLabResultListItemDto:
    result_id: str
    title: str
    date: str | None
    status: str
    has_pdf: bool
    lab_name: str | None
    clinic_name: str | None
    short_services_summary: str | None


@dataclass(frozen=True, slots=True)
class PatientLabResultDetailsDto:
    result_id: str
    title: str
    date: str | None
    status: str
    has_pdf: bool
    lab_name: str | None
    clinic_name: str | None
    services: list[str]
    sections: list[dict[str, Any]]
    indicators: list[dict[str, Any]]
    pdf_open_url: str | None
    pdf_download_url: str | None


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
        normalized: list[PatientLabResultListItemDto] = []
        for item in payload:
            try:
                normalized.append(_map_result_list_item(item))
            except PatientLabResultNotFoundError:
                continue
        return normalized

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
        return _map_result_details(payload, requested_result_id=result_id)

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
    result_id = _resolve_result_id(raw)
    if not result_id:
        raise PatientLabResultNotFoundError("В payload списка отсутствует result_id")
    services = _extract_services(raw)
    return PatientLabResultListItemDto(
        result_id=result_id,
        title=_resolve_title(raw, services),
        date=_first_optional_str(raw, "date") or _format_date(_first_optional_str(raw, "datetime", "date_time", "created_at")),
        status=_normalize_status(raw),
        has_pdf=_has_pdf(raw),
        lab_name=_first_optional_str(raw, "lab", "lab_name"),
        clinic_name=_first_optional_str(raw, "clinic", "clinic_name"),
        short_services_summary=_build_short_services_summary(services),
    )


def _map_result_details(raw: dict[str, Any], *, requested_result_id: str) -> PatientLabResultDetailsDto:
    result_id = _resolve_result_id(raw, fallback=requested_result_id)
    if not result_id:
        raise PatientLabResultNotFoundError("В payload details отсутствует result_id")
    services = _extract_services(raw)
    has_pdf = _has_pdf(raw)
    pdf_route = f"/patient/results/{result_id}/pdf"
    return PatientLabResultDetailsDto(
        result_id=result_id,
        title=_resolve_title(raw, services),
        date=_first_optional_str(raw, "date") or _format_date(_first_optional_str(raw, "datetime", "date_time", "created_at")),
        status=_normalize_status(raw),
        has_pdf=has_pdf,
        lab_name=_first_optional_str(raw, "lab", "lab_name"),
        clinic_name=_first_optional_str(raw, "clinic", "clinic_name"),
        services=services,
        sections=_extract_list(raw, "sections", "result_sections"),
        indicators=_extract_list(raw, "indicators", "result_indicators", "results"),
        pdf_open_url=pdf_route if has_pdf else None,
        pdf_download_url=pdf_route if has_pdf else None,
    )


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


def _has_pdf(raw: dict[str, Any]) -> bool:
    if _first_bool(raw, "has_pdf", "is_pdf_available"):
        return True
    files = raw.get("files")
    if isinstance(files, list):
        for item in files:
            if isinstance(item, str) and item.strip():
                return True
            if isinstance(item, dict) and _first_optional_str(item, "url", "file_url", "pdf_url", "link"):
                return True
    files_count = _first_int(raw, "files_count", "pdf_count")
    if files_count is not None and files_count > 0:
        return True
    documents = _extract_list(raw, "documents", "pdfs")
    for doc in documents:
        if _first_optional_str(doc, "url", "file_url", "pdf_url", "link"):
            return True
    return False


def _normalize_status(raw: dict[str, Any]) -> str:
    raw_status = (_first_optional_str(raw, "status", "result_status") or "").lower()
    mapping = {
        "ready": "Готов",
        "completed": "Готов",
        "done": "Готов",
        "pending": "В обработке",
        "in_progress": "В обработке",
        "processing": "В обработке",
    }
    if raw_status in mapping:
        return mapping[raw_status]
    if _first_bool(raw, "is_ready", "ready", "is_completed"):
        return "Готов"
    if _first_optional_str(raw, "ready_at", "completed_at", "validated_at"):
        return "Готов"
    return "В обработке"


def _resolve_result_id(raw: dict[str, Any], *, fallback: str = "") -> str:
    return _first_str(raw, "result_id", "id", "lab_result_id", default=fallback.strip())


def _resolve_title(raw: dict[str, Any], services: list[str]) -> str:
    explicit = _first_optional_str(raw, "title", "name", "result_name")
    if explicit:
        return explicit
    if services:
        return f"Результаты: {services[0]}"
    return "Лабораторный результат"


def _build_short_services_summary(services: list[str]) -> str | None:
    if not services:
        return None
    if len(services) == 1:
        return services[0]
    return f"{services[0]} + ещё {len(services) - 1}"


def _format_date(value: str | None) -> str | None:
    dt = _parse_datetime(value)
    if dt is None:
        return None
    return dt.date().isoformat()


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


def _first_bool(raw: dict[str, Any], *keys: str) -> bool:
    truthy = {"1", "true", "yes", "y", "да"}
    falsy = {"0", "false", "no", "n", "нет"}
    for key in keys:
        value = raw.get(key)
        if isinstance(value, bool):
            return value
        if value is None:
            continue
        text = str(value).strip().lower()
        if text in truthy:
            return True
        if text in falsy:
            return False
    return False


def _first_int(raw: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = raw.get(key)
        if value is None:
            continue
        try:
            return int(str(value).strip())
        except ValueError:
            continue
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
