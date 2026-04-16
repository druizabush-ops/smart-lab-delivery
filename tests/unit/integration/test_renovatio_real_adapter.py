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
        "https://renovatio.local/api/1/getPatientLabResults",
        "https://renovatio.local/api/1/getPatientLabResultDetails",
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
