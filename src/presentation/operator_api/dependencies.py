"""Dependency providers для operator API."""

from fastapi import Depends, Request

from src.application.services import DeliveryCardReadService
from src.application.use_cases import (
    MoveToManualReviewCommandUseCase,
    OverrideChannelCommandUseCase,
    RequeueDeliveryCardCommandUseCase,
    RetryDeliveryCardCommandUseCase,
)


class OperatorApiDependencyError(RuntimeError):
    """Ошибка конфигурации зависимостей operator API."""


def get_read_service(request: Request) -> DeliveryCardReadService:
    """Возвращает DeliveryCardReadService из app.state контейнера."""

    service = getattr(request.app.state, "delivery_card_read_service", None)
    if service is None:
        raise OperatorApiDependencyError(
            "delivery_card_read_service не инициализирован в app.state"
        )
    return service


ReadServiceDep = Depends(get_read_service)


def get_retry_command_use_case(request: Request) -> RetryDeliveryCardCommandUseCase:
    use_case = getattr(request.app.state, "retry_delivery_card_command_use_case", None)
    if use_case is None:
        raise OperatorApiDependencyError("retry_delivery_card_command_use_case не инициализирован в app.state")
    return use_case


def get_manual_review_command_use_case(request: Request) -> MoveToManualReviewCommandUseCase:
    use_case = getattr(request.app.state, "move_to_manual_review_command_use_case", None)
    if use_case is None:
        raise OperatorApiDependencyError("move_to_manual_review_command_use_case не инициализирован в app.state")
    return use_case


def get_requeue_command_use_case(request: Request) -> RequeueDeliveryCardCommandUseCase:
    use_case = getattr(request.app.state, "requeue_delivery_card_command_use_case", None)
    if use_case is None:
        raise OperatorApiDependencyError("requeue_delivery_card_command_use_case не инициализирован в app.state")
    return use_case


def get_override_channel_command_use_case(request: Request) -> OverrideChannelCommandUseCase:
    use_case = getattr(request.app.state, "override_channel_command_use_case", None)
    if use_case is None:
        raise OperatorApiDependencyError("override_channel_command_use_case не инициализирован в app.state")
    return use_case
