import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, LabResultStatus
from src.infrastructure.identity import build_operational_card_id
from src.infrastructure.repositories import InMemoryDeliveryCardRepository
from src.presentation.operator_api import create_operator_api_app


def _build_card(patient_id: str, lab_result_id: str) -> DeliveryCard:
    patient = Patient(id=patient_id, full_name="Test User", email="test@example.org")
    result = LabResult(id=lab_result_id, patient_id=patient_id, status=LabResultStatus.READY)
    return DeliveryCard.create(patient=patient, lab_result=result, channel=DeliveryChannel.MAX)


def _build_client(repository) -> TestClient:
    class _Container:
        def __init__(self):
            self.delivery_card_repository = repository
            self.retry_delivery_card_command_use_case = None
            self.move_to_manual_review_command_use_case = None
            self.requeue_delivery_card_command_use_case = None
            self.override_channel_command_use_case = None

    return TestClient(create_operator_api_app(container=_Container()))


def test_patient_results_list_and_detail_isolated_from_operator_contract() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card("patient-001", "lr-1")
    card.add_attempt(
        DeliveryAttempt(
            timestamp=card.created_at,
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.SUCCESS,
        )
    )
    repository.save(card)
    repository.save(_build_card("patient-002", "lr-2"))

    client = _build_client(repository)
    response = client.get("/patient/results", params={"patient_id": "patient-001"})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["patient_id"] == "patient-001"
    assert "attempts_count" in payload[0]
    assert "attempts" not in payload[0]

    result_id = payload[0]["result_id"]
    detail = client.get(f"/patient/results/{result_id}", params={"patient_id": "patient-001"})
    assert detail.status_code == 200
    assert detail.json()["documents"][0]["readiness"] == "ready"


def test_patient_result_returns_404_for_foreign_patient_or_unknown_result() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card("patient-777", "lr-777")
    repository.save(card)
    card_id = build_operational_card_id(card)
    client = _build_client(repository)

    foreign_response = client.get(f"/patient/results/{card_id}", params={"patient_id": "patient-other"})
    assert foreign_response.status_code == 404

    unknown_response = client.get("/patient/results/unknown", params={"patient_id": "patient-777"})
    assert unknown_response.status_code == 404
