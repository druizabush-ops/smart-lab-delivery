"""Тесты mapping и обработки ошибок в real Renovatio adapter."""

import httpx
import pytest
from urllib.parse import parse_qsl

from src.config.integration_settings import RenovatioSettings
from src.domain.statuses import LabResultStatus
from src.integration.errors import IntegrationFailure
from src.integration.renovatio import RenovatioClient


def test_real_renovatio_maps_ready_results_from_api_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        form = dict(parse_qsl(request.content.decode()))
        method = form.get("method")
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
