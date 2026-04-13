import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.application.services import DeliveryCardReadService
from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, LabResultStatus, QueueStatus
from src.infrastructure.identity import build_operational_card_id
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.repositories import PostgresDeliveryCardRepository
from src.infrastructure.repositories import InMemoryDeliveryCardRepository
from src.presentation.operator_api import create_operator_api_app


def _build_card(
    patient_id: str,
    lab_result_id: str,
    channel: DeliveryChannel = DeliveryChannel.MAX,
) -> DeliveryCard:
    patient = Patient(id=patient_id, full_name="Test User", email="test@example.org")
    result = LabResult(id=lab_result_id, patient_id=patient_id, status=LabResultStatus.READY)
    return DeliveryCard.create(patient=patient, lab_result=result, channel=channel)


def _build_client(repository) -> TestClient:
    class _Container:
        def __init__(self):
            self.delivery_card_repository = repository
            self.delivery_card_read_service = DeliveryCardReadService(repository=repository)

    app = create_operator_api_app(container=_Container())
    return TestClient(app)


def test_operator_cards_list_and_filter_status() -> None:
    repository = InMemoryDeliveryCardRepository()

    card_ok = _build_card("p-1", "lr-1")
    repository.save(card_ok)

    card_failed = _build_card("p-2", "lr-2")
    card_failed.add_attempt(
        DeliveryAttempt(
            timestamp=card_failed.created_at,
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.ERROR,
            error_message="network",
        )
    )
    repository.save(card_failed)

    client = _build_client(repository)

    all_response = client.get("/operator/cards")
    assert all_response.status_code == 200
    assert len(all_response.json()) == 2

    failed_response = client.get("/operator/cards", params={"status": "failed"})
    assert failed_response.status_code == 200
    payload = failed_response.json()
    assert len(payload) == 1
    assert payload[0]["status"] == "failed"


def test_operator_get_card_by_id_and_summary() -> None:
    repository = InMemoryDeliveryCardRepository()

    card = _build_card("p-1", "lr-100")
    repository.save(card)
    card_id = build_operational_card_id(card)

    review_card = _build_card("p-2", "lr-200")
    review_card.change_queue_status(QueueStatus.MANUAL_REVIEW)
    repository.save(review_card)

    client = _build_client(repository)

    response = client.get(f"/operator/cards/{card_id}")
    assert response.status_code == 200
    assert response.json()["card_id"] == card_id

    summary_response = client.get("/operator/cards/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_cards"] == 2
    assert summary["manual_review_count"] == 1


def test_operator_api_handles_empty_storage() -> None:
    client = _build_client(InMemoryDeliveryCardRepository())

    list_response = client.get("/operator/cards")
    assert list_response.status_code == 200
    assert list_response.json() == []

    summary_response = client.get("/operator/cards/summary")
    assert summary_response.status_code == 200
    assert summary_response.json()["total_cards"] == 0


def test_operator_api_works_with_postgres_repository() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    repository = PostgresDeliveryCardRepository(session_factory=factory)

    card = _build_card("p-postgres", "lr-postgres")
    repository.save(card)

    client = _build_client(repository)
    response = client.get("/operator/cards")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["patient_id"] == "p-postgres"
