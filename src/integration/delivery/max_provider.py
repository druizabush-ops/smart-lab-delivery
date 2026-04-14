"""Адаптер отправки через MAX: stub и реальный transport-контур."""

from datetime import datetime

import httpx

from src.application.interfaces import DeliveryProvider
from src.config.integration_settings import MaxSettings
from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel
from src.domain.statuses import AttemptStatus
from src.integration.errors import IntegrationErrorKind, IntegrationFailure


class MaxDeliveryProvider(DeliveryProvider):
    """Провайдер доставки в MAX с dual-mode и базовой обработкой ошибок."""

    _STUB_FAILURE_RESULT_IDS = frozenset({"lr-ready-002"})

    def __init__(
        self,
        *,
        mode: str = "stub",
        settings: MaxSettings | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._mode = mode
        self._settings = settings or MaxSettings.from_env()
        self._http_client = http_client or httpx.Client(timeout=self._settings.timeout_seconds)

    def send(self, card: DeliveryCard) -> DeliveryAttempt:
        if card.channel is not DeliveryChannel.MAX:
            return self._error_attempt("MAX provider получил карточку с неподдерживаемым каналом.")

        if self._mode != "real":
            if card.lab_result_id in self._STUB_FAILURE_RESULT_IDS:
                return self._error_attempt("MAX stub: имитация временной ошибки отправки.")
            return DeliveryAttempt(timestamp=datetime.utcnow(), channel=DeliveryChannel.MAX, result=AttemptStatus.SUCCESS)

        try:
            recipient_id = self._resolve_recipient_id(card)
            payload = self._build_message_payload(recipient_id=recipient_id, card=card)
            self._send_payload(payload)
            return DeliveryAttempt(timestamp=datetime.utcnow(), channel=DeliveryChannel.MAX, result=AttemptStatus.SUCCESS)
        except IntegrationFailure as exc:
            return self._error_attempt(str(exc))

    def build_deep_link(self, card: DeliveryCard) -> str:
        """Формирует контракт deep-link для mini app открытия результата."""

        if not self._settings.bot_name:
            return ""
        payload = f"lab_result:{card.lab_result_id}|patient:{card.patient_id}"
        return f"https://max.ru/{self._settings.bot_name}?startapp={payload}"

    def _resolve_recipient_id(self, card: DeliveryCard) -> str:
        """Возвращает MAX recipient_id для пациента в real-режиме отправки.

        # TEMP: identity mapping (patient_id → MAX user_id)
        # В реальной системе должен быть вынесен в отдельный identity/service слой.
        """

        recipient_id = self._settings.patient_recipient_map.get(card.patient_id, "")
        if recipient_id:
            return recipient_id
        raise IntegrationFailure(
            IntegrationErrorKind.DELIVERY_MAX,
            "MAX recipient id не найден для patient_id (tech debt: отсутствует identity mapping).",
        )

    def _build_message_payload(self, *, recipient_id: str, card: DeliveryCard) -> dict:
        """Собирает JSON payload для /messages в MAX API."""

        return {
            "recipient": {"user_id": recipient_id},
            "message": {
                "text": (
                    "Ваш лабораторный результат готов. "
                    f"Откройте карточку результата: {self.build_deep_link(card)}"
                )
            },
        }

    def _send_payload(self, payload: dict) -> None:
        if not self._settings.bot_token:
            raise IntegrationFailure(IntegrationErrorKind.CONFIG, "MAX bot token не задан для real режима.")

        url = f"{self._settings.base_url.rstrip('/')}/messages"
        headers = {
            "Authorization": self._settings.bot_token,
            "Content-Type": "application/json",
        }

        try:
            response = self._http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise IntegrationFailure(IntegrationErrorKind.TIMEOUT, "MAX timeout.") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {401, 403}:
                raise IntegrationFailure(IntegrationErrorKind.AUTH, "MAX auth failure.") from exc
            raise IntegrationFailure(
                IntegrationErrorKind.DELIVERY_MAX,
                f"MAX delivery status: {exc.response.status_code}.",
            ) from exc
        except httpx.HTTPError as exc:
            raise IntegrationFailure(
                IntegrationErrorKind.DELIVERY_MAX,
                "MAX transport error.",
            ) from exc

    @staticmethod
    def _error_attempt(message: str) -> DeliveryAttempt:
        return DeliveryAttempt(
            timestamp=datetime.utcnow(),
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.ERROR,
            error_message=message,
        )
