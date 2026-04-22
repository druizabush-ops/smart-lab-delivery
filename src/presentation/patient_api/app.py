"""Фабрика FastAPI-приложения для patient-facing mini app API."""

from fastapi import FastAPI

from src.config.container import AppContainer
from src.presentation.common.errors import register_error_handlers
from src.presentation.common.health import HealthService, build_health_router
from src.presentation.common.middleware import CorrelationIdMiddleware, SimpleRateLimitMiddleware
from src.presentation.patient_api.routers.auth import router as auth_router
from src.presentation.patient_api.routers.results import router as results_router


def create_patient_api_app(container: AppContainer | None = None) -> FastAPI:
    app_container = container or AppContainer()
    app = FastAPI(
        title="Smart Lab Delivery Patient API",
        version="0.1.0",
        root_path="/api/patient",
    )
    app.state.security_settings = app_container.security_settings
    app.state.patient_results_use_case = app_container.patient_results_use_case
    app.state.patient_result_pdf_use_case = app_container.patient_result_pdf_use_case
    app.state.patient_login_use_case = app_container.patient_login_use_case
    app.state.patient_phone_login_use_case = app_container.patient_phone_login_use_case
    app.state.confirm_patient_auth_code_use_case = app_container.confirm_patient_auth_code_use_case
    app.state.refresh_patient_session_use_case = app_container.refresh_patient_session_use_case
    app.state.get_current_patient_use_case = app_container.get_current_patient_use_case
    app.state.bind_patient_session_use_case = app_container.bind_patient_session_use_case
    app.state.resolve_bound_patient_session_use_case = app_container.resolve_bound_patient_session_use_case
    app.state.unbind_patient_session_use_case = app_container.unbind_patient_session_use_case
    app.state.patient_session_repository = app_container.patient_session_repository
    app.state.renovatio_settings = app_container.renovatio_settings
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        SimpleRateLimitMiddleware,
        enabled=app_container.security_settings.rate_limit_enabled,
        limit_per_minute=app_container.security_settings.rate_limit_per_minute,
    )
    register_error_handlers(app)
    app.include_router(build_health_router(HealthService(app_container)))
    app.include_router(auth_router)
    app.include_router(results_router)
    return app
