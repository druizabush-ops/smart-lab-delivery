"""Интеграционный адаптер Renovatio: stub и real HTTP-режим."""

from datetime import datetime, timedelta
from typing import Any

import httpx

from src.application.interfaces import LabResultProvider
from src.config.integration_settings import RenovatioSettings
from src.domain.entities import LabResult
from src.domain.statuses import LabResultStatus
from src.integration.errors import IntegrationErrorKind, IntegrationFailure


class RenovatioClient(LabResultProvider):
    """Адаптер к Renovatio c поддержкой dual-mode (stub/real)."""
    # Временное решение: один адаптер поддерживает stub и real режим.
    # В будущем может быть разделено на отдельные реализации.

    def __init__(
        self,
        *,
        mode: str = "stub",
        settings: RenovatioSettings | None = None,
        seed_results: list[LabResult] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._mode = mode
        self._settings = settings or RenovatioSettings.from_env()
        self._seed_results = seed_results or self._build_default_results()
        self._http_client = http_client or httpx.Client(timeout=self._settings.timeout_seconds)

    def get_ready_results(self) -> list[LabResult]:
        """Возвращает готовые результаты: из заглушки или из реального Renovatio API."""

        if self._mode != "real":
            return [result for result in self._seed_results if result.status is LabResultStatus.READY]

        ready_results: list[LabResult] = []
        for patient_id in self._settings.seed_patient_ids:
            patient = self.get_patient(patient_id)
            for item in self.get_patient_lab_results(patient_id=patient["id"]):
                details = self.get_patient_lab_result_details(item["id"])
                result = self._to_lab_result(patient_id=patient["id"], raw_result=details)
                if result.status is LabResultStatus.READY:
                    ready_results.append(result)
        return ready_results

    def get_patient(self, patient_id: str) -> dict[str, Any]:
        """Возвращает нормализованную карточку пациента из Renovatio."""

        data = self._call_api("getPatient", {"patient_id": patient_id})
        if not data:
            raise IntegrationFailure(IntegrationErrorKind.EMPTY_RESULT, "Renovatio: пациент не найден.")
        patient = data[0] if isinstance(data, list) else data
        return {
            "id": str(patient.get("id") or patient.get("patient_id") or patient_id),
            "full_name": str(patient.get("full_name") or patient.get("name") or ""),
        }

    def get_patient_lab_results(self, patient_id: str) -> list[dict[str, Any]]:
        """Возвращает список лабораторных результатов пациента."""

        data = self._call_api("getPatientLabResults", {"patient_id": patient_id})
        if not isinstance(data, list):
            raise IntegrationFailure(
                IntegrationErrorKind.BAD_RESPONSE,
                "Renovatio: список результатов должен быть массивом.",
            )
        return [{"id": str(item.get("id") or item.get("result_id") or "")} for item in data if item]

    def get_patient_lab_result_details(self, lab_result_id: str) -> dict[str, Any]:
        """Возвращает подробности лабораторного результата из Renovatio."""

        data = self._call_api("getPatientLabResultDetails", {"lab_result_id": lab_result_id})
        if not data:
            raise IntegrationFailure(
                IntegrationErrorKind.EMPTY_RESULT,
                "Renovatio: детали лабораторного результата отсутствуют.",
            )
        return data[0] if isinstance(data, list) else data

    def _call_api(self, method_name: str, payload: dict[str, Any]) -> Any:
        """Выполняет form-urlencoded запрос в Renovatio и извлекает поле data.

        Для real режима используется фактический HTTP-контракт Renovatio:
        POST <base_url>/<api_version>/<method> или POST <base_url>/<method>.
        """

        if not self._settings.api_key:
            raise IntegrationFailure(
                IntegrationErrorKind.CONFIG,
                "Renovatio API key не задан для real режима.",
            )

        body: dict[str, Any] = {
            "api_key": self._settings.api_key,
            **payload,
        }
        method_url = self._build_method_url(method_name)

        try:
            response = self._http_client.post(method_url, data=body)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise IntegrationFailure(IntegrationErrorKind.TIMEOUT, "Renovatio timeout.") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {401, 403}:
                raise IntegrationFailure(IntegrationErrorKind.AUTH, "Renovatio auth failure.") from exc
            raise IntegrationFailure(
                IntegrationErrorKind.BAD_RESPONSE,
                f"Renovatio HTTP status: {exc.response.status_code}.",
            ) from exc
        except httpx.HTTPError as exc:
            raise IntegrationFailure(IntegrationErrorKind.BAD_RESPONSE, "Renovatio HTTP transport error.") from exc

        try:
            parsed = response.json()
        except ValueError as exc:
            raise IntegrationFailure(
                IntegrationErrorKind.BAD_RESPONSE,
                "Renovatio вернул невалидный JSON.",
            ) from exc

        error = parsed.get("error")
        if error:
            raise IntegrationFailure(IntegrationErrorKind.BAD_RESPONSE, f"Renovatio error: {error}")

        return parsed.get("data")

    def _build_method_url(self, method_name: str) -> str:
        """Строит URL метода Renovatio по real HTTP-контракту."""

        base_url = self._settings.base_url.rstrip("/")
        api_version = self._settings.api_version.strip()
        if api_version:
            return f"{base_url}/{api_version}/{method_name}"
        return f"{base_url}/{method_name}"

    @staticmethod
    def _to_lab_result(patient_id: str, raw_result: dict[str, Any]) -> LabResult:
        """Преобразует внешний формат Renovatio в доменную сущность LabResult."""

        raw_status = str(raw_result.get("status") or raw_result.get("state") or "").strip().lower()
        is_ready_flag = raw_result.get("is_ready")

        if raw_status in {"ready", "completed", "done"} or is_ready_flag in {True, 1, "1"}:
            status = LabResultStatus.READY
        else:
            status = LabResultStatus.PENDING

        collected_at = None
        raw_collected_at = raw_result.get("collected_at")
        if isinstance(raw_collected_at, str) and raw_collected_at:
            try:
                collected_at = datetime.fromisoformat(raw_collected_at.replace("Z", "+00:00"))
            except ValueError:
                collected_at = None

        return LabResult(
            id=str(raw_result.get("id") or raw_result.get("result_id") or ""),
            patient_id=patient_id,
            status=status,
            collected_at=collected_at,
        )

    @staticmethod
    def _build_default_results() -> list[LabResult]:
        now = datetime.utcnow()
        return [
            LabResult(
                id="lr-ready-001",
                patient_id="patient-001",
                status=LabResultStatus.READY,
                collected_at=now - timedelta(hours=2),
            ),
            LabResult(
                id="lr-ready-002",
                patient_id="patient-002",
                status=LabResultStatus.READY,
                collected_at=now - timedelta(hours=1),
            ),
            LabResult(
                id="lr-pending-003",
                patient_id="patient-003",
                status=LabResultStatus.PENDING,
                collected_at=now - timedelta(minutes=30),
            ),
        ]
