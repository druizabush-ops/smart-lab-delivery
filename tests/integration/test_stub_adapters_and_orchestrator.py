from src.config.container import AppContainer
from src.domain.entities import DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, DeliveryStatus, LabResultStatus, QueueStatus
from src.integration.delivery import EmailDeliveryProvider, MaxDeliveryProvider
from src.integration.renovatio import RenovatioClient


def test_renovatio_returns_only_ready_results() -> None:
    client = RenovatioClient(
        seed_results=[
            LabResult(id="lr-ready", patient_id="p-1", status=LabResultStatus.READY),
            LabResult(id="lr-pending", patient_id="p-2", status=LabResultStatus.PENDING),
        ]
    )

    ready = client.get_ready_results()

    assert len(ready) == 1
    assert ready[0].id == "lr-ready"
    assert all(result.status is LabResultStatus.READY for result in ready)


def test_max_and_email_providers_are_deterministic_and_return_attempts() -> None:
    patient = Patient(id="patient-001", full_name="Ivan", email="ivan@example.com")
    ready = LabResult(id="lr-1", patient_id="patient-001", status=LabResultStatus.READY)

    max_success_card = DeliveryCard.create(patient, ready, DeliveryChannel.MAX)
    max_error_card = DeliveryCard.create(
        patient,
        LabResult(id="lr-ready-002", patient_id="patient-001", status=LabResultStatus.READY),
        DeliveryChannel.MAX,
    )

    max_provider = MaxDeliveryProvider()
    success_attempt = max_provider.send(max_success_card)
    error_attempt = max_provider.send(max_error_card)

    assert success_attempt.result is AttemptStatus.SUCCESS
    assert error_attempt.result is AttemptStatus.ERROR

    email_provider = EmailDeliveryProvider()
    email_success = email_provider.send(DeliveryCard.create(patient, ready, DeliveryChannel.EMAIL))
    email_error_patient = Patient(id="patient-003", full_name="Petr", email="petr@example.com")
    email_error = email_provider.send(
        DeliveryCard.create(
            email_error_patient,
            LabResult(id="lr-3", patient_id="patient-003", status=LabResultStatus.READY),
            DeliveryChannel.EMAIL,
        )
    )

    assert email_success.result is AttemptStatus.SUCCESS
    assert email_error.result is AttemptStatus.ERROR


def test_app_container_builds_and_orchestrates_ready_results_end_to_end() -> None:
    container = AppContainer()
    assert container.delivery_orchestrator is not None

    patients = {
        "patient-001": Patient(id="patient-001", full_name="One", email="one@example.com"),
        "patient-002": Patient(id="patient-002", full_name="Two", email="two@example.com"),
    }

    cards = container.delivery_orchestrator.orchestrate_ready_results(patients)

    assert len(cards) == 2
    statuses = {card.lab_result_id: card.status for card in cards}
    assert statuses["lr-ready-001"] is DeliveryStatus.MAX_SENT
    assert statuses["lr-ready-002"] is DeliveryStatus.NOT_STARTED


def test_orchestrator_retry_failure_pipeline_keeps_architecture_consistent() -> None:
    container = AppContainer()
    patients = {
        "patient-001": Patient(id="patient-001", full_name="One", email="one@example.com"),
        "patient-002": Patient(id="patient-002", full_name="Two", email="two@example.com"),
    }
    initial_cards = container.delivery_orchestrator.orchestrate_ready_results(patients)
    failed_card = next(card for card in initial_cards if card.lab_result_id == "lr-ready-002")

    assert failed_card.channel is DeliveryChannel.EMAIL
    assert failed_card.status is DeliveryStatus.NOT_STARTED

    retried = container.delivery_orchestrator.orchestrate_retry(failed_card)

    assert retried.status is DeliveryStatus.EMAIL_SENT
    assert retried.queue_status is QueueStatus.DONE
    assert len(retried.attempts) >= 2
