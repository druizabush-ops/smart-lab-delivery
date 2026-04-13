"""Фабрика FastAPI-приложения для operator read-only API."""

from fastapi import FastAPI

from src.application.services import DeliveryCardReadService
from src.config.container import AppContainer
from src.presentation.operator_api.routers.cards import router as cards_router


def create_operator_api_app(container: AppContainer | None = None) -> FastAPI:
    """Собирает FastAPI приложение с read-only стеком operator API."""

    app_container = container or AppContainer()
    app = FastAPI(title="Smart Lab Delivery Operator API", version="0.1.0")
    app.state.delivery_card_read_service = DeliveryCardReadService(
        repository=app_container.delivery_card_repository
    )
    app.include_router(cards_router)
    return app
