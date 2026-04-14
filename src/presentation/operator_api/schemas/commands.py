"""Pydantic-схемы command-side operator API."""

from pydantic import BaseModel, Field


class MoveToManualReviewRequest(BaseModel):
    """Тело запроса на перевод карточки в manual_review."""

    reason: str | None = Field(default=None, max_length=500)


class RequeueCardRequest(BaseModel):
    """Тело запроса на requeue карточки."""

    reason: str | None = Field(default=None, max_length=500)


class OverrideChannelRequest(BaseModel):
    """Тело запроса на ручной override канала доставки."""

    channel: str
    reason: str | None = Field(default=None, max_length=500)


class RetryCardCommandResponse(BaseModel):
    """Ответ на retry-команду."""

    card_id: str
    status: str
    queue_status: str
    channel: str
    message: str


class MoveToManualReviewResponse(BaseModel):
    """Ответ на перевод в manual_review."""

    card_id: str
    status: str
    queue_status: str
    channel: str
    message: str


class RequeueCardResponse(BaseModel):
    """Ответ на requeue-команду."""

    card_id: str
    status: str
    queue_status: str
    channel: str
    message: str


class OverrideChannelResponse(BaseModel):
    """Ответ на override канала."""

    card_id: str
    status: str
    queue_status: str
    channel: str
    message: str
