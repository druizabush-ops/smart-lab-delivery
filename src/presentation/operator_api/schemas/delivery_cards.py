"""Pydantic-схемы операторского read-only API по карточкам доставки."""

from datetime import datetime

from pydantic import BaseModel


class DeliveryAttemptResponse(BaseModel):
    """Ответ с данными одной попытки отправки."""

    sequence_no: int
    timestamp: datetime
    channel: str
    result: str
    error_message: str | None = None


class DeliveryCardResponse(BaseModel):
    """Ответ с карточкой доставки для operator API."""

    card_id: str
    patient_id: str
    lab_result_id: str
    status: str
    queue_status: str
    channel: str
    created_at: datetime
    updated_at: datetime
    attempts: list[DeliveryAttemptResponse]


class DeliveryCardSummaryResponse(BaseModel):
    """Сводный read-only ответ по состояниям карточек."""

    total_cards: int
    active_count: int
    done_count: int
    manual_review_count: int
    exhausted_count: int
    failed_count: int
