"""Фабрика FastAPI-приложения для operator read + command API."""

from fastapi import FastAPI

from src.application.services import DeliveryCardReadService
from src.config.container import AppContainer
from src.presentation.operator_api.routers.cards import router as cards_router
from src.presentation.operator_api.routers.commands import router as commands_router


def create_operator_api_app(container: AppContainer | None = None) -> FastAPI:
    """Собирает FastAPI приложение с разделением read-only и command-side стека."""

    app_container = container or AppContainer()
    app = FastAPI(title="Smart Lab Delivery Operator API", version="0.1.0")
    app.state.delivery_card_read_service = DeliveryCardReadService(
        repository=app_container.delivery_card_repository
    )
    app.state.retry_delivery_card_command_use_case = app_container.retry_delivery_card_command_use_case
    app.state.move_to_manual_review_command_use_case = app_container.move_to_manual_review_command_use_case
    app.state.requeue_delivery_card_command_use_case = app_container.requeue_delivery_card_command_use_case
    app.state.override_channel_command_use_case = app_container.override_channel_command_use_case
    app.include_router(cards_router)
    app.include_router(commands_router)
    return app
