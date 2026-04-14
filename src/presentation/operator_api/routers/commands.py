"""Command-side endpoints operator API для управляемых действий."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.application.use_cases.operator_commands import OperatorCommandError
from src.application.use_cases import (
    MoveToManualReviewCommandUseCase,
    OverrideChannelCommandUseCase,
    RequeueDeliveryCardCommandUseCase,
    RetryDeliveryCardCommandUseCase,
)
from src.domain.entities import DeliveryChannel
from src.presentation.operator_api.dependencies import (
    get_manual_review_command_use_case,
    get_override_channel_command_use_case,
    get_requeue_command_use_case,
    get_retry_command_use_case,
)
from src.presentation.operator_api.schemas.commands import (
    MoveToManualReviewRequest,
    MoveToManualReviewResponse,
    OverrideChannelRequest,
    OverrideChannelResponse,
    RequeueCardRequest,
    RequeueCardResponse,
    RetryCardCommandResponse,
)

router = APIRouter(prefix="/operator/cards", tags=["operator-card-commands"])


@router.post("/{card_id}/retry", response_model=RetryCardCommandResponse)
def retry_card(
    card_id: str,
    use_case: Annotated[RetryDeliveryCardCommandUseCase, Depends(get_retry_command_use_case)],
) -> RetryCardCommandResponse:
    """Операторский retry карточки доставки."""

    try:
        result = use_case.execute(card_id)
    except OperatorCommandError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return RetryCardCommandResponse.model_validate(result, from_attributes=True)


@router.post("/{card_id}/manual-review", response_model=MoveToManualReviewResponse)
def move_to_manual_review(
    card_id: str,
    request: MoveToManualReviewRequest,
    use_case: Annotated[MoveToManualReviewCommandUseCase, Depends(get_manual_review_command_use_case)],
) -> MoveToManualReviewResponse:
    """Операторский перевод карточки в manual_review."""

    try:
        result = use_case.execute(card_id=card_id, reason=request.reason)
    except OperatorCommandError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return MoveToManualReviewResponse.model_validate(result, from_attributes=True)


@router.post("/{card_id}/requeue", response_model=RequeueCardResponse)
def requeue_card(
    card_id: str,
    request: RequeueCardRequest,
    use_case: Annotated[RequeueDeliveryCardCommandUseCase, Depends(get_requeue_command_use_case)],
) -> RequeueCardResponse:
    """Операторский возврат карточки в активную очередь обработки."""

    try:
        result = use_case.execute(card_id=card_id, reason=request.reason)
    except OperatorCommandError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return RequeueCardResponse.model_validate(result, from_attributes=True)


@router.post("/{card_id}/override-channel", response_model=OverrideChannelResponse)
def override_channel(
    card_id: str,
    request: OverrideChannelRequest,
    use_case: Annotated[OverrideChannelCommandUseCase, Depends(get_override_channel_command_use_case)],
) -> OverrideChannelResponse:
    """Операторская смена канала доставки карточки."""

    try:
        channel = DeliveryChannel(request.channel)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Недопустимый канал доставки.") from exc

    try:
        result = use_case.execute(card_id=card_id, channel=channel, reason=request.reason)
    except OperatorCommandError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return OverrideChannelResponse.model_validate(result, from_attributes=True)
