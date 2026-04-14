"""Тесты deterministic поведения интеграционных адаптеров в stub-режиме."""

from src.domain.entities import DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, LabResultStatus
from src.integration.delivery import EmailDeliveryProvider, MaxDeliveryProvider
from src.integration.renovatio import RenovatioClient


def _build_card(*, channel: DeliveryChannel, patient_id: str, lab_result_id: str) -> DeliveryCard:
    patient = Patient(id=patient_id, full_name="Тест")
    result = LabResult(id=lab_result_id, patient_id=patient_id, status=LabResultStatus.READY)
    return DeliveryCard.create(patient, result, channel)


def test_max_stub_has_deterministic_failure_set() -> None:
    provider = MaxDeliveryProvider(mode="stub")

    success_attempt = provider.send(
        _build_card(channel=DeliveryChannel.MAX, patient_id="patient-001", lab_result_id="lr-ready-001")
    )
    error_attempt = provider.send(
        _build_card(channel=DeliveryChannel.MAX, patient_id="patient-001", lab_result_id="lr-ready-002")
    )

    assert success_attempt.result is AttemptStatus.SUCCESS
    assert error_attempt.result is AttemptStatus.ERROR


def test_email_stub_has_deterministic_failure_set() -> None:
    provider = EmailDeliveryProvider(mode="stub")

    success_attempt = provider.send(
        _build_card(channel=DeliveryChannel.EMAIL, patient_id="patient-001", lab_result_id="lr-ready-001")
    )
    error_attempt = provider.send(
        _build_card(channel=DeliveryChannel.EMAIL, patient_id="patient-003", lab_result_id="lr-ready-003")
    )

    assert success_attempt.result is AttemptStatus.SUCCESS
    assert error_attempt.result is AttemptStatus.ERROR


def test_renovatio_stub_uses_seed_results_only() -> None:
    provider = RenovatioClient(
        mode="stub",
        seed_results=[
            LabResult(id="lr-ready", patient_id="patient-1", status=LabResultStatus.READY),
            LabResult(id="lr-pending", patient_id="patient-1", status=LabResultStatus.PENDING),
        ],
    )

    ready = provider.get_ready_results()

    assert [item.id for item in ready] == ["lr-ready"]
