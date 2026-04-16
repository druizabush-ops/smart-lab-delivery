import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from src.config.security_settings import SecuritySettings
from src.infrastructure.repositories import InMemoryDeliveryCardRepository
from src.presentation.operator_api import create_operator_api_app
from src.presentation.patient_api import create_patient_api_app


class _Container:
    def __init__(self) -> None:
        self.delivery_card_repository = InMemoryDeliveryCardRepository()
        self.retry_delivery_card_command_use_case = None
        self.move_to_manual_review_command_use_case = None
        self.requeue_delivery_card_command_use_case = None
        self.override_channel_command_use_case = None
        self.security_settings = SecuritySettings.from_env()
        class Runtime:
            repository_mode = "in_memory"
            integration_mode = "stub"
            environment = "test"
        self.runtime_settings = Runtime()


def test_health_endpoints_available() -> None:
    client = TestClient(create_operator_api_app(container=_Container()))

    live = client.get("/health/live")
    ready = client.get("/health/ready")

    assert live.status_code == 200
    assert ready.status_code == 200
    assert ready.json()["status"] in {"ready", "not_ready"}


def test_root_path_docs_and_openapi_available_for_nginx_prefixes() -> None:
    operator_client = TestClient(create_operator_api_app(container=_Container()))
    patient_client = TestClient(create_patient_api_app(container=_Container()))

    operator_docs = operator_client.get("/docs")
    patient_docs = patient_client.get("/docs")
    operator_openapi = operator_client.get("/openapi.json")
    patient_openapi = patient_client.get("/openapi.json")

    assert operator_docs.status_code == 200
    assert "/api/operator/openapi.json" in operator_docs.text
    assert patient_docs.status_code == 200
    assert "/api/patient/openapi.json" in patient_docs.text

    assert operator_openapi.status_code == 200
    assert patient_openapi.status_code == 200
    assert operator_openapi.json()["servers"][0]["url"] == "/api/operator"
    assert patient_openapi.json()["servers"][0]["url"] == "/api/patient"


def test_patient_endpoint_rejects_unsafe_context_in_strict_mode(monkeypatch) -> None:
    monkeypatch.setenv("SLD_PATIENT_SECURITY_MODE", "strict")
    client = TestClient(create_operator_api_app(container=_Container()))

    response = client.get("/patient/results", params={"patient_id": "patient-001"})

    assert response.status_code == 401
    assert response.json()["code"] == "http_error"
