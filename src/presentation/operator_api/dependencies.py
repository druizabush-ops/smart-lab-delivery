"""Dependency providers для operator API."""

from fastapi import Depends, Request

from src.application.services import DeliveryCardReadService


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
