"""Тесты построения transport-запроса MAX в real-режиме."""

import httpx

from src.config.integration_settings import MaxSettings
from src.domain.entities import DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, LabResultStatus
from src.integration.delivery import MaxDeliveryProvider


def _build_card() -> DeliveryCard:
    patient = Patient(id="patient-001", full_name="Иван")
    lab_result = LabResult(id="lr-001", patient_id="patient-001", status=LabResultStatus.READY)
    return DeliveryCard.create(patient, lab_result, DeliveryChannel.MAX)


def test_max_real_provider_builds_request_with_authorization_header() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("Authorization")
        captured["json"] = request.content.decode()
        return httpx.Response(200, json={"ok": True})

    settings = MaxSettings(
        base_url="https://platform-api.max.ru",
        bot_token="token-value",
        timeout_seconds=2,
        bot_name="smartlabbot",
        patient_recipient_map={"patient-001": "max-user-1"},
    )
    provider = MaxDeliveryProvider(
        mode="real",
        settings=settings,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    attempt = provider.send(_build_card())

    assert attempt.result is AttemptStatus.SUCCESS
    assert captured["url"].endswith("/messages")
    assert captured["auth"] == "token-value"
    assert "max-user-1" in captured["json"]


def test_max_real_provider_returns_error_when_mapping_missing() -> None:
    settings = MaxSettings(
        base_url="https://platform-api.max.ru",
        bot_token="token-value",
        timeout_seconds=2,
        bot_name="smartlabbot",
        patient_recipient_map={},
    )
    provider = MaxDeliveryProvider(mode="real", settings=settings)

    attempt = provider.send(_build_card())

    assert attempt.result is AttemptStatus.ERROR
    assert attempt.error_message
    assert "tech debt" in attempt.error_message
