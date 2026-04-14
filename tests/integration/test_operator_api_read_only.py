import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.application.services import DeduplicationPolicy, DeliveryPolicy, FallbackPolicy, RetryLimits, RetryPolicy
from src.application.services import DeliveryCardReadService
from src.application.services.policies import OperatorActionPolicy
from src.application.use_cases import (
    HandleDeliveryFailureUseCase,
    OverrideChannelCommandUseCase,
    RegisterDeliveryResultUseCase,
    RequeueDeliveryCardCommandUseCase,
    RetryDeliveryCardCommandUseCase,
    RetryDeliveryUseCase,
    MoveToManualReviewCommandUseCase,
)
from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, DeliveryStatus, LabResultStatus, QueueStatus
from src.infrastructure.identity import build_operational_card_id
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.repositories import PostgresDeliveryCardRepository
from src.infrastructure.repositories import InMemoryDeliveryCardRepository
from src.presentation.operator_api import create_operator_api_app
from src.config.security_settings import SecuritySettings


class _AlwaysSuccessProvider:
    def __init__(self, channel: DeliveryChannel) -> None:
        self._channel = channel

    def send(self, card: DeliveryCard) -> DeliveryAttempt:
        return DeliveryAttempt(
            timestamp=card.updated_at,
            channel=self._channel,
            result=AttemptStatus.SUCCESS,
        )


def _build_card(
    patient_id: str,
    lab_result_id: str,
    channel: DeliveryChannel = DeliveryChannel.MAX,
) -> DeliveryCard:
    patient = Patient(id=patient_id, full_name="Test User", email="test@example.org")
    result = LabResult(id=lab_result_id, patient_id=patient_id, status=LabResultStatus.READY)
    return DeliveryCard.create(patient=patient, lab_result=result, channel=channel)


def _build_client(repository) -> TestClient:
    delivery_policy = DeliveryPolicy(
        retry_policy=RetryPolicy(RetryLimits(max_total_attempts=4, max_max_attempts=2, max_email_attempts=2)),
        fallback_policy=FallbackPolicy(),
        deduplication_policy=DeduplicationPolicy(),
    )
    retry_uc = RetryDeliveryUseCase(
        max_delivery_provider=_AlwaysSuccessProvider(DeliveryChannel.MAX),
        email_delivery_provider=_AlwaysSuccessProvider(DeliveryChannel.EMAIL),
        delivery_policy=delivery_policy,
        register_result_use_case=RegisterDeliveryResultUseCase(),
        failure_use_case=HandleDeliveryFailureUseCase(delivery_policy=delivery_policy),
    )

    class _Container:
        def __init__(self):
            self.delivery_card_repository = repository
            self.delivery_card_read_service = DeliveryCardReadService(repository=repository)
            self.retry_delivery_card_command_use_case = RetryDeliveryCardCommandUseCase(
                repository=repository,
                policy=OperatorActionPolicy(),
                retry_use_case=retry_uc,
            )
            self.move_to_manual_review_command_use_case = MoveToManualReviewCommandUseCase(
                repository=repository,
                policy=OperatorActionPolicy(),
            )
            self.requeue_delivery_card_command_use_case = RequeueDeliveryCardCommandUseCase(
                repository=repository,
                policy=OperatorActionPolicy(),
            )
            self.override_channel_command_use_case = OverrideChannelCommandUseCase(
                repository=repository,
                policy=OperatorActionPolicy(),
            )
            self.security_settings = SecuritySettings.from_env()

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
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
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


def test_operator_command_endpoints_update_card_state() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card("p-cmd", "lr-cmd")
    card_id = build_operational_card_id(card)
    repository.save(card)
    client = _build_client(repository)

    manual = client.post(f"/operator/cards/{card_id}/manual-review", json={"reason": "ручная проверка"})
    assert manual.status_code == 200
    assert manual.json()["queue_status"] == QueueStatus.MANUAL_REVIEW.value

    override = client.post(
        f"/operator/cards/{card_id}/override-channel",
        json={"channel": DeliveryChannel.EMAIL.value, "reason": "переключение"},
    )
    assert override.status_code == 200
    assert override.json()["channel"] == DeliveryChannel.EMAIL.value

    requeue = client.post(f"/operator/cards/{card_id}/requeue", json={"reason": "возврат"})
    assert requeue.status_code == 200
    assert requeue.json()["queue_status"] == QueueStatus.ACTIVE.value

    read_after = client.get(f"/operator/cards/{card_id}")
    assert read_after.status_code == 200
    assert read_after.json()["queue_status"] == QueueStatus.ACTIVE.value
    assert read_after.json()["channel"] == DeliveryChannel.EMAIL.value


def test_operator_command_endpoint_returns_409_for_forbidden_action() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card("p-deny", "lr-deny")
    card.add_attempt(
        DeliveryAttempt(
            timestamp=card.created_at,
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.SUCCESS,
        )
    )
    card_id = build_operational_card_id(card)
    repository.save(card)
    client = _build_client(repository)

    response = client.post(f"/operator/cards/{card_id}/requeue", json={"reason": "нельзя"})
    assert response.status_code == 409


def test_operator_command_endpoints_return_4xx_for_invalid_override_and_retry() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card("p-override", "lr-override", channel=DeliveryChannel.MAX)
    card_id = build_operational_card_id(card)
    repository.save(card)
    client = _build_client(repository)

    same_channel = client.post(
        f"/operator/cards/{card_id}/override-channel",
        json={"channel": DeliveryChannel.MAX.value, "reason": "тот же канал"},
    )
    assert same_channel.status_code == 409

    card.add_attempt(
        DeliveryAttempt(
            timestamp=card.created_at,
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.SUCCESS,
        )
    )
    repository.update(card)
    assert card.status in {DeliveryStatus.MAX_SENT, DeliveryStatus.EMAIL_SENT}

    terminal_override = client.post(
        f"/operator/cards/{card_id}/override-channel",
        json={"channel": DeliveryChannel.EMAIL.value, "reason": "терминальный"},
    )
    assert terminal_override.status_code == 409

    terminal_retry = client.post(f"/operator/cards/{card_id}/retry")
    assert terminal_retry.status_code == 409
