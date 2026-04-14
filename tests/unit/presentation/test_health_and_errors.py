import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.config.security_settings import SecuritySettings
from src.presentation.common.errors import register_error_handlers
from src.presentation.common.health import HealthService, build_health_router


class _Container:
    def __init__(self, repository_mode: str = "in_memory") -> None:
        class Runtime:
            environment = "test"
            integration_mode = "stub"

        self.runtime_settings = Runtime()
        self.runtime_settings.repository_mode = repository_mode
        self.security_settings = SecuritySettings.from_env()
        self._session_factory = None


def test_health_ready_returns_ready_for_in_memory_mode() -> None:
    app = FastAPI()
    app.include_router(build_health_router(HealthService(_Container())))
    client = TestClient(app)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_unified_error_response_schema() -> None:
    app = FastAPI()

    @app.get("/boom")
    def boom():
        raise HTTPException(status_code=409, detail="Конфликт")

    register_error_handlers(app)
    client = TestClient(app)

    response = client.get("/boom")

    assert response.status_code == 409
    payload = response.json()
    assert payload["code"] == "http_error"
    assert payload["message"] == "Конфликт"
    assert payload["correlation_id"]
