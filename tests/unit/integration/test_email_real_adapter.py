"""Тесты real email adapter без сетевых вызовов."""

from src.config.integration_settings import EmailSettings
from src.domain.entities import DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, LabResultStatus
from src.integration.delivery import EmailDeliveryProvider


def _build_card(*, patient_id: str = "patient-010", lab_result_id: str = "lr-010") -> DeliveryCard:
    patient = Patient(id=patient_id, full_name="Анна")
    lab_result = LabResult(id=lab_result_id, patient_id=patient_id, status=LabResultStatus.READY)
    return DeliveryCard.create(patient, lab_result, DeliveryChannel.EMAIL)


def test_email_real_provider_builds_subject_and_sender(monkeypatch) -> None:
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            sent["host"] = host
            sent["port"] = port
            sent["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            sent["tls"] = True

        def login(self, username, password):
            sent["login"] = (username, password)

        def send_message(self, message):
            sent["subject"] = message["Subject"]
            sent["from"] = message["From"]
            sent["to"] = message["To"]

    monkeypatch.setattr("src.integration.delivery.email_provider.smtplib.SMTP", FakeSMTP)

    settings = EmailSettings(
        smtp_host="smtp.local",
        smtp_port=2525,
        username="user",
        password="pass",
        from_address="lab@local",
        use_tls=True,
        timeout_seconds=3,
    )
    provider = EmailDeliveryProvider(mode="real", settings=settings)

    attempt = provider.send(_build_card(patient_id="patient-003"))

    assert attempt.result is AttemptStatus.SUCCESS
    assert sent["host"] == "smtp.local"
    assert sent["from"] == "lab@local"
    assert "lr-010" in sent["subject"]
