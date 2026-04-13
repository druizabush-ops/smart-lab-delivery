"""Read-only endpoints operator API для карточек доставки."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.services import DeliveryCardQueryFilters, DeliveryCardReadService
from src.presentation.operator_api.dependencies import get_read_service
from src.presentation.operator_api.schemas.delivery_cards import (
    DeliveryCardResponse,
    DeliveryCardSummaryResponse,
)

router = APIRouter(prefix="/operator/cards", tags=["operator-cards"])


@router.get("", response_model=list[DeliveryCardResponse])
def list_cards(
    status: str | None = Query(default=None),
    queue_status: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    patient_id: str | None = Query(default=None),
    lab_result_id: str | None = Query(default=None),
    only_active: bool = Query(default=False),
    only_done: bool = Query(default=False),
    read_service: Annotated[DeliveryCardReadService, Depends(get_read_service)] = None,
) -> list[DeliveryCardResponse]:
    """Возвращает список карточек с базовыми фильтрами."""

    cards = read_service.list_cards(
        DeliveryCardQueryFilters(
            status=status,
            queue_status=queue_status,
            channel=channel,
            patient_id=patient_id,
            lab_result_id=lab_result_id,
            only_active=only_active,
            only_done=only_done,
        )
    )
    return [DeliveryCardResponse.model_validate(card, from_attributes=True) for card in cards]


@router.get("/summary", response_model=DeliveryCardSummaryResponse)
def get_summary(
    read_service: Annotated[DeliveryCardReadService, Depends(get_read_service)] = None,
) -> DeliveryCardSummaryResponse:
    """Возвращает сводку по состояниям карточек доставки."""

    summary = read_service.build_summary()
    return DeliveryCardSummaryResponse.model_validate(summary, from_attributes=True)


@router.get("/{card_id}", response_model=DeliveryCardResponse)
def get_card_by_id(
    card_id: str,
    read_service: Annotated[DeliveryCardReadService, Depends(get_read_service)] = None,
) -> DeliveryCardResponse:
    """Возвращает карточку доставки по идентификатору."""

    card = read_service.get_card(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Карточка не найдена")
    return DeliveryCardResponse.model_validate(card, from_attributes=True)
