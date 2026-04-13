"""Stub-адаптер к Renovatio без реального HTTP."""

from datetime import datetime, timedelta

from src.application.interfaces import LabResultProvider
from src.domain.entities import LabResult
from src.domain.statuses import LabResultStatus


class RenovatioClient(LabResultProvider):
    """Возвращает готовые лабораторные результаты из in-memory заглушки."""

    def __init__(self, seed_results: list[LabResult] | None = None) -> None:
        self._seed_results = seed_results or self._build_default_results()

    def get_ready_results(self) -> list[LabResult]:
        """Возвращает только результаты со статусом READY."""

        return [result for result in self._seed_results if result.status is LabResultStatus.READY]

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
