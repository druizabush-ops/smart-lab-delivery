"""Read-only сервис пациентского контекста mini app."""

from dataclasses import dataclass
from datetime import datetime

from src.application.interfaces import DeliveryCardRepository
from src.infrastructure.identity import build_operational_card_id


@dataclass(frozen=True, slots=True)
class PatientResultDocumentReadModel:
    """Документ результата, доступный пациенту."""

    title: str
    url: str | None
    readiness: str


@dataclass(frozen=True, slots=True)
class PatientResultReadModel:
    """Упрощенная read-model карточки для patient mini app."""

    result_id: str
    patient_id: str
    status: str
    channel: str
    created_at: datetime
    updated_at: datetime
    attempts_count: int
    last_error: str | None
    documents: list[PatientResultDocumentReadModel]


class PatientResultReadService:
    """Изолирует patient-facing read-контракт от operator API модели."""

    def __init__(self, repository: DeliveryCardRepository) -> None:
        self._repository = repository

    def list_results(self, patient_id: str) -> list[PatientResultReadModel]:
        cards = [card for card in self._repository.list_all() if card.patient_id == patient_id]
        models = [self._to_read_model(card) for card in cards]
        return sorted(models, key=lambda item: item.created_at, reverse=True)

    def get_result(self, patient_id: str, result_id: str) -> PatientResultReadModel | None:
        card = self._repository.get_by_id(result_id)
        if card is None or card.patient_id != patient_id:
            return None
        return self._to_read_model(card)

    @staticmethod
    def _to_read_model(card) -> PatientResultReadModel:
        card_id = build_operational_card_id(card)
        document_ready = card.status.value in {"max_sent", "email_sent"}
        return PatientResultReadModel(
            result_id=card_id,
            patient_id=card.patient_id,
            status=card.status.value,
            channel=card.channel.value,
            created_at=card.created_at,
            updated_at=card.updated_at,
            attempts_count=len(card.attempts),
            last_error=card.attempts[-1].error_message if card.attempts else None,
            documents=[
                PatientResultDocumentReadModel(
                    title="Результат исследования (PDF)",
                    url=f"/patient/results/{card_id}/document" if document_ready else None,
                    readiness="ready" if document_ready else "pending",
                )
            ],
        )
