"""Тесты real Renovatio adapter: контракт URL/body, mapping и ошибки."""

import httpx
import pytest
from urllib.parse import parse_qsl

from src.config.integration_settings import RenovatioSettings
from src.domain.statuses import LabResultStatus
from src.integration.errors import IntegrationFailure
from src.integration.renovatio import RenovatioClient


def test_real_renovatio_maps_ready_results_from_api_payload() -> None:
    request_urls: list[str] = []
    request_bodies: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        request_urls.append(str(request.url))
        form = dict(parse_qsl(request.content.decode()))
        request_bodies.append(form)
        method = request.url.path.split("/")[-1]
        if method == "getPatient":
            return httpx.Response(200, json={"error": None, "data": {"id": "patient-42", "name": "P"}})
        if method == "getPatientLabResults":
            return httpx.Response(200, json={"error": None, "data": [{"id": "lr-42"}]})
        return httpx.Response(200, json={"error": None, "data": {"id": "lr-42", "status": "ready"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = RenovatioSettings(
        base_url="https://renovatio.local/api",
        api_key="key",
        api_version="1",
        timeout_seconds=2,
        seed_patient_ids=("patient-42",),
    )

    adapter = RenovatioClient(mode="real", settings=settings, http_client=client)

    results = adapter.get_ready_results()

    assert len(results) == 1
    assert results[0].id == "lr-42"
    assert results[0].status is LabResultStatus.READY
    assert request_urls == [
        "https://renovatio.local/api/1/getPatient",
        "https://renovatio.local/api/getPatientLabResults",
        "https://renovatio.local/api/getPatientLabResultDetails",
    ]
    assert all("method" not in body for body in request_bodies)
    assert all(body.get("api_key") == "key" for body in request_bodies)


def test_real_renovatio_builds_url_without_version_when_version_is_empty() -> None:
    captured_url = ""
    captured_body: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_url, captured_body
        captured_url = str(request.url)
        captured_body = dict(parse_qsl(request.content.decode()))
        return httpx.Response(200, json={"error": None, "data": {"id": "patient-1", "name": "P"}})

    adapter = RenovatioClient(
        mode="real",
        settings=RenovatioSettings("https://renovatio.local/api", "key", "", 2, ("patient-1",)),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    adapter.get_patient("patient-1")

    assert captured_url == "https://renovatio.local/api/getPatient"
    assert captured_body["api_key"] == "key"
    assert captured_body["id"] == "patient-1"
    assert "method" not in captured_body


def test_real_renovatio_raises_on_api_error_field() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": "bad_key", "data": None})

    adapter = RenovatioClient(
        mode="real",
        settings=RenovatioSettings("https://renovatio.local/api", "key", "1", 2, ("patient-1",)),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(IntegrationFailure):
        adapter.get_patient("patient-1")


def test_real_renovatio_auth_patient_uses_login_password_payload() -> None:
    captured_body: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        captured_body = dict(parse_qsl(request.content.decode()))
        return httpx.Response(200, json={"error": None, "data": {"patient_id": "p-1"}})

    adapter = RenovatioClient(
        mode="real",
        settings=RenovatioSettings("https://renovatio.local/api", "key", "1", 2, ("patient-1",)),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = adapter.auth_patient(login="demo", password="secret")

    assert response["patient_id"] == "p-1"
    assert captured_body["login"] == "demo"
    assert captured_body["password"] == "secret"
    assert "phone" not in captured_body


def test_real_renovatio_auth_patient_uses_phone_payload() -> None:
    captured_body: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        captured_body = dict(parse_qsl(request.content.decode()))
        return httpx.Response(200, json={"error": None, "data": {"need_auth_key": 1}})

    adapter = RenovatioClient(
        mode="real",
        settings=RenovatioSettings("https://renovatio.local/api", "key", "1", 2, ("patient-1",)),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = adapter.auth_patient(phone="+70000000000")

    assert response["need_auth_key"] == 1
    assert captured_body["phone"] == "+70000000000"
    assert "login" not in captured_body
    assert "password" not in captured_body


def test_real_renovatio_check_auth_code_uses_patient_id_and_auth_code() -> None:
    captured_body: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        captured_body = dict(parse_qsl(request.content.decode()))
        return httpx.Response(200, json={"error": None, "data": {"patient_key": "pk-1"}})

    adapter = RenovatioClient(
        mode="real",
        settings=RenovatioSettings("https://renovatio.local/api", "key", "1", 2, ("patient-1",)),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = adapter.check_auth_code(patient_id="patient-1", auth_code="1234")

    assert response["patient_key"] == "pk-1"
    assert captured_body["patient_id"] == "patient-1"
    assert captured_body["auth_code"] == "1234"


def test_real_renovatio_get_patient_info_uses_patient_key() -> None:
    captured_url = ""
    captured_body: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_url, captured_body
        captured_url = str(request.url)
        captured_body = dict(parse_qsl(request.content.decode()))
        return httpx.Response(200, json={"error": None, "data": {"id": "patient-1", "name": "P"}})

    adapter = RenovatioClient(
        mode="real",
        settings=RenovatioSettings("https://renovatio.local/api", "key", "1", 2, ("patient-1",)),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = adapter.get_patient_info("pk-1")

    assert response["id"] == "patient-1"
    assert captured_url == "https://renovatio.local/api/getPatientInfo"
    assert captured_body["patient_key"] == "pk-1"


def test_real_renovatio_get_patient_lab_results_by_key_uses_patient_key() -> None:
    captured_url = ""
    captured_body: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_url, captured_body
        captured_url = str(request.url)
        captured_body = dict(parse_qsl(request.content.decode()))
        return httpx.Response(200, json={"error": None, "data": [{"id": "lr-1"}]})

    adapter = RenovatioClient(
        mode="real",
        settings=RenovatioSettings("https://renovatio.local/api", "key", "1", 2, ("patient-1",)),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = adapter.get_patient_lab_results_by_key(
        "pk-1",
        date_from="2026-01-01",
        date_to="2026-01-31",
        lab_id="lab-1",
        clinic_id="clinic-1",
    )

    assert response[0]["id"] == "lr-1"
    assert captured_url == "https://renovatio.local/api/getPatientLabResults"
    assert captured_body["patient_key"] == "pk-1"
    assert captured_body["date_from"] == "2026-01-01"
    assert captured_body["date_to"] == "2026-01-31"
    assert captured_body["lab_id"] == "lab-1"
    assert captured_body["clinic_id"] == "clinic-1"


def test_real_renovatio_get_patient_lab_result_details_by_key_uses_result_id_and_patient_key() -> None:
    captured_url = ""
    captured_body: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_url, captured_body
        captured_url = str(request.url)
        captured_body = dict(parse_qsl(request.content.decode()))
        return httpx.Response(200, json={"error": None, "data": {"id": "lr-1", "status": "ready"}})

    adapter = RenovatioClient(
        mode="real",
        settings=RenovatioSettings("https://renovatio.local/api", "key", "1", 2, ("patient-1",)),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = adapter.get_patient_lab_result_details_by_key(
        "pk-1",
        "result-1",
        patient_id="patient-1",
        lab_id="lab-1",
        clinic_id="clinic-1",
    )

    assert response["id"] == "lr-1"
    assert captured_url == "https://renovatio.local/api/getPatientLabResultDetails"
    assert captured_body["patient_key"] == "pk-1"
    assert captured_body["result_id"] == "result-1"
    assert captured_body["patient_id"] == "patient-1"
    assert captured_body["lab_id"] == "lab-1"
    assert captured_body["clinic_id"] == "clinic-1"


def test_patient_facing_methods_raise_controlled_error_in_stub_mode() -> None:
    adapter = RenovatioClient(
        mode="stub",
        settings=RenovatioSettings("https://renovatio.local/api", "key", "1", 2, ("patient-1",)),
    )

    with pytest.raises(IntegrationFailure) as exc_info:
        adapter.get_patient_info("pk-1")

    assert "только в real режиме" in str(exc_info.value)


def test_real_renovatio_routes_auth_patient_without_version() -> None:
    captured_url = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_url
        captured_url = str(request.url)
        return httpx.Response(200, json={"error": None, "data": {"patient_key": "pk-1"}})

    adapter = RenovatioClient(
        mode="real",
        settings=RenovatioSettings("https://renovatio.local/api", "key", "1", 2, ("patient-1",)),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    adapter.auth_patient_by_login(login="demo", password="secret")

    assert captured_url == "https://renovatio.local/api/authPatient"


def test_real_renovatio_reports_method_routing_mismatch() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": 1, "data": {"code": "404", "desc": "Method not found"}})

    adapter = RenovatioClient(
        mode="real",
        settings=RenovatioSettings("https://renovatio.local/api", "key", "1", 2, ("patient-1",)),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(IntegrationFailure) as exc_info:
        adapter.get_patient_info("pk-1")

    assert "routing mismatch" in str(exc_info.value)
