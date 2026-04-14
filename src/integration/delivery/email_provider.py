"""Адаптер email-доставки: stub и реальная SMTP-отправка."""

from datetime import datetime
from email.message import EmailMessage
import smtplib

from src.application.interfaces import DeliveryProvider
from src.config.integration_settings import EmailSettings
from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel
from src.domain.statuses import AttemptStatus
from src.integration.errors import IntegrationErrorKind, IntegrationFailure


class EmailDeliveryProvider(DeliveryProvider):
    """Провайдер email-отправки с dual-mode и централизованным mapping ошибок."""

    _STUB_FAILURE_PATIENT_IDS = frozenset({"patient-003"})

    def __init__(self, *, mode: str = "stub", settings: EmailSettings | None = None) -> None:
        self._mode = mode
        self._settings = settings or EmailSettings.from_env()

    def send(self, card: DeliveryCard) -> DeliveryAttempt:
        if card.channel is not DeliveryChannel.EMAIL:
            return self._error_attempt("Email provider получил карточку с неподдерживаемым каналом.")

        if self._mode != "real":
            if card.patient_id in self._STUB_FAILURE_PATIENT_IDS:
                return self._error_attempt("EMAIL stub: имитация недоступности SMTP-провайдера.")
            return DeliveryAttempt(timestamp=datetime.utcnow(), channel=DeliveryChannel.EMAIL, result=AttemptStatus.SUCCESS)

        try:
            message = self._build_message(card)
            self._send_message(message)
            return DeliveryAttempt(timestamp=datetime.utcnow(), channel=DeliveryChannel.EMAIL, result=AttemptStatus.SUCCESS)
        except IntegrationFailure as exc:
            return self._error_attempt(str(exc))

    def _build_message(self, card: DeliveryCard) -> EmailMessage:
        """Строит subject/body для уведомления пациента о готовом результате."""

        message = EmailMessage()
        to_address = f"{card.patient_id}@patients.local"
        message["From"] = self._settings.from_address
        message["To"] = to_address
        message["Subject"] = f"Результат анализов готов ({card.lab_result_id})"
        message.set_content(
            "Здравствуйте! Ваш лабораторный результат готов. "
            f"Идентификатор результата: {card.lab_result_id}."
        )
        return message

    def _send_message(self, message: EmailMessage) -> None:
        if not self._settings.smtp_host:
            raise IntegrationFailure(IntegrationErrorKind.CONFIG, "SMTP host не задан для real режима.")

        try:
            with smtplib.SMTP(
                host=self._settings.smtp_host,
                port=self._settings.smtp_port,
                timeout=self._settings.timeout_seconds,
            ) as server:
                if self._settings.use_tls:
                    server.starttls()
                if self._settings.username:
                    server.login(self._settings.username, self._settings.password)
                server.send_message(message)
        except TimeoutError as exc:
            raise IntegrationFailure(IntegrationErrorKind.TIMEOUT, "Email SMTP timeout.") from exc
        except smtplib.SMTPAuthenticationError as exc:
            raise IntegrationFailure(IntegrationErrorKind.AUTH, "Email auth failure.") from exc
        except smtplib.SMTPException as exc:
            raise IntegrationFailure(
                IntegrationErrorKind.DELIVERY_EMAIL,
                f"Email SMTP failure: {exc}",
            ) from exc

    @staticmethod
    def _error_attempt(message: str) -> DeliveryAttempt:
        return DeliveryAttempt(
            timestamp=datetime.utcnow(),
            channel=DeliveryChannel.EMAIL,
            result=AttemptStatus.ERROR,
            error_message=message,
        )
