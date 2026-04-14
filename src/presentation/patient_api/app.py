"""Фабрика FastAPI-приложения для patient-facing mini app API."""

from fastapi import FastAPI

from src.application.services import PatientResultReadService
from src.config.container import AppContainer
from src.presentation.patient_api.routers.results import router as results_router


def create_patient_api_app(container: AppContainer | None = None) -> FastAPI:
    app_container = container or AppContainer()
    app = FastAPI(title="Smart Lab Delivery Patient API", version="0.1.0")
    app.state.patient_result_read_service = PatientResultReadService(
        repository=app_container.delivery_card_repository,
    )
    app.include_router(results_router)
    return app
