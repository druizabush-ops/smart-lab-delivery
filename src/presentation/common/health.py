"""Health/readiness endpoints и сервис проверок."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter
from sqlalchemy import text


@dataclass(frozen=True, slots=True)
class ReadinessStatus:
    """Сводка readiness проверок."""

    app_ok: bool
    db_ok: bool
    config_ok: bool
    integration_mode_ok: bool

    @property
    def ready(self) -> bool:
        return self.app_ok and self.db_ok and self.config_ok and self.integration_mode_ok


class HealthService:
    """Сервис базовых readiness проверок без запуска бизнес-логики."""

    def __init__(self, container) -> None:
        self._container = container

    def get_readiness(self) -> ReadinessStatus:
        runtime = self._container.runtime_settings
        config_ok = runtime.environment in {"dev", "test", "staging", "prod"}
        integration_mode_ok = runtime.integration_mode in {"stub", "real"}
        db_ok = self._check_db()
        return ReadinessStatus(app_ok=True, db_ok=db_ok, config_ok=config_ok, integration_mode_ok=integration_mode_ok)

    def _check_db(self) -> bool:
        if self._container.runtime_settings.repository_mode != "postgres":
            return True
        session_factory = getattr(self._container, "_session_factory", None)
        if session_factory is None:
            return False
        try:
            with session_factory() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False


def build_health_router(health_service: HealthService) -> APIRouter:
    """Создает роутер health/live и health/ready."""

    router = APIRouter(prefix="/health", tags=["health"])

    @router.get("/live")
    def live() -> dict[str, str]:
        return {"status": "live"}

    @router.get("/ready")
    def ready() -> dict[str, object]:
        status = health_service.get_readiness()
        return {
            "status": "ready" if status.ready else "not_ready",
            "checks": {
                "app": status.app_ok,
                "db": status.db_ok,
                "config": status.config_ok,
                "integration_mode": status.integration_mode_ok,
            },
        }

    return router
