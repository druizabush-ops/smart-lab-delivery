"""Фабрика FastAPI-приложения для patient-facing mini app API."""

from fastapi import FastAPI

from src.application.services import PatientResultReadService
from src.config.container import AppContainer
from src.presentation.common.errors import register_error_handlers
from src.presentation.common.health import HealthService, build_health_router
from src.presentation.common.middleware import CorrelationIdMiddleware, SimpleRateLimitMiddleware
from src.presentation.patient_api.routers.results import router as results_router


def create_patient_api_app(container: AppContainer | None = None) -> FastAPI:
    app_container = container or AppContainer()
    app = FastAPI(title="Smart Lab Delivery Patient API", version="0.1.0")
    app.state.security_settings = app_container.security_settings
    app.state.patient_result_read_service = PatientResultReadService(
        repository=app_container.delivery_card_repository,
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        SimpleRateLimitMiddleware,
        enabled=app_container.security_settings.rate_limit_enabled,
        limit_per_minute=app_container.security_settings.rate_limit_per_minute,
    )
    register_error_handlers(app)
    app.include_router(build_health_router(HealthService(app_container)))
    app.include_router(results_router)
    return app
