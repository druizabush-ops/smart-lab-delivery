"""Доменная сущность лабораторного результата."""

from dataclasses import dataclass, replace
from datetime import datetime

from src.domain.statuses import LabResultStatus


@dataclass(frozen=True, slots=True)
class LabResult:
    """Лабораторный результат, полученный из Renovatio.

    Инварианты:
    - Идентификаторы результата и пациента не пустые.
    - Статус хранится только через LabResultStatus.

    Ограничения:
    - Переход к статусу MISSING_PDF разрешен только если READY уже был достигнут.
    """

    id: str
    patient_id: str
    status: LabResultStatus
    collected_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Идентификатор результата не может быть пустым.")
        if not self.patient_id.strip():
            raise ValueError("Идентификатор пациента в результате не может быть пустым.")

    def change_status(self, new_status: LabResultStatus) -> "LabResult":
        """Возвращает новую версию сущности с валидным переходом статуса."""

        allowed_transitions: dict[LabResultStatus, set[LabResultStatus]] = {
            LabResultStatus.PENDING: {LabResultStatus.READY, LabResultStatus.BLOCKED},
            LabResultStatus.READY: {LabResultStatus.MISSING_PDF, LabResultStatus.BLOCKED},
            LabResultStatus.MISSING_PDF: set(),
            LabResultStatus.BLOCKED: set(),
        }

        if new_status == self.status:
            return self

        if new_status not in allowed_transitions[self.status]:
            raise ValueError(
                f"Запрещенный переход статуса результата: {self.status} -> {new_status}."
            )

        return replace(self, status=new_status)
