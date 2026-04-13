"""Read-only query сервис для операторского доступа к карточкам доставки."""

from dataclasses import dataclass
from datetime import datetime

from src.application.interfaces import DeliveryCardRepository
from src.domain.entities.delivery_attempt import DeliveryAttempt
from src.domain.statuses import DeliveryStatus, QueueStatus
from src.infrastructure.identity import build_operational_card_id


@dataclass(frozen=True, slots=True)
class DeliveryAttemptReadModel:
    """Read-model одной попытки доставки для API-ответа."""

    sequence_no: int
    timestamp: datetime
    channel: str
    result: str
    error_message: str | None


@dataclass(frozen=True, slots=True)
class DeliveryCardReadModel:
    """Read-model карточки доставки для операторского API."""

    card_id: str
    patient_id: str
    lab_result_id: str
    status: str
    queue_status: str
    channel: str
    created_at: datetime
    updated_at: datetime
    attempts: list[DeliveryAttemptReadModel]


@dataclass(frozen=True, slots=True)
class DeliveryCardSummaryReadModel:
    """Агрегированная сводка по состоянию карточек доставки."""

    total_cards: int
    active_count: int
    done_count: int
    manual_review_count: int
    exhausted_count: int
    failed_count: int


@dataclass(frozen=True, slots=True)
class DeliveryCardQueryFilters:
    """Фильтры выборки карточек для read-only API."""

    status: str | None = None
    queue_status: str | None = None
    channel: str | None = None
    patient_id: str | None = None
    lab_result_id: str | None = None
    only_active: bool = False
    only_done: bool = False


class DeliveryCardReadService:
    """Изолирует query-доступ к карточкам доставки от presentation-слоя."""

    def __init__(self, repository: DeliveryCardRepository) -> None:
        self._repository = repository

    def list_cards(self, filters: DeliveryCardQueryFilters) -> list[DeliveryCardReadModel]:
        cards = [self._to_read_model(card) for card in self._repository.list_all()]

        if filters.status:
            cards = [card for card in cards if card.status == filters.status]
        if filters.queue_status:
            cards = [card for card in cards if card.queue_status == filters.queue_status]
        if filters.channel:
            cards = [card for card in cards if card.channel == filters.channel]
        if filters.patient_id:
            cards = [card for card in cards if card.patient_id == filters.patient_id]
        if filters.lab_result_id:
            cards = [card for card in cards if card.lab_result_id == filters.lab_result_id]
        if filters.only_active:
            cards = [card for card in cards if card.queue_status == QueueStatus.ACTIVE.value]
        if filters.only_done:
            cards = [card for card in cards if card.queue_status == QueueStatus.DONE.value]

        return sorted(cards, key=lambda card: card.created_at)

    def get_card(self, card_id: str) -> DeliveryCardReadModel | None:
        card = self._repository.get_by_id(card_id)
        if card is None:
            return None
        return self._to_read_model(card)

    def build_summary(self) -> DeliveryCardSummaryReadModel:
        cards = [self._to_read_model(card) for card in self._repository.list_all()]
        return DeliveryCardSummaryReadModel(
            total_cards=len(cards),
            active_count=sum(card.queue_status == QueueStatus.ACTIVE.value for card in cards),
            done_count=sum(card.queue_status == QueueStatus.DONE.value for card in cards),
            manual_review_count=sum(card.queue_status == QueueStatus.MANUAL_REVIEW.value for card in cards),
            exhausted_count=sum(card.status == DeliveryStatus.EXHAUSTED.value for card in cards),
            failed_count=sum(card.status == DeliveryStatus.FAILED.value for card in cards),
        )

    @staticmethod
    def _to_read_model(card) -> DeliveryCardReadModel:
        return DeliveryCardReadModel(
            card_id=build_operational_card_id(card),
            patient_id=card.patient_id,
            lab_result_id=card.lab_result_id,
            status=card.status.value,
            queue_status=card.queue_status.value,
            channel=card.channel.value,
            created_at=card.created_at,
            updated_at=card.updated_at,
            attempts=[
                DeliveryCardReadService._to_attempt_read_model(index, attempt)
                for index, attempt in enumerate(card.attempts)
            ],
        )

    @staticmethod
    def _to_attempt_read_model(index: int, attempt: DeliveryAttempt) -> DeliveryAttemptReadModel:
        return DeliveryAttemptReadModel(
            sequence_no=index,
            timestamp=attempt.timestamp,
            channel=attempt.channel.value,
            result=attempt.result.value,
            error_message=attempt.error_message,
        )
