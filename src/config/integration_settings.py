"""Конфигурация реальных интеграций (Renovatio, MAX, Email)."""

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class RenovatioSettings:
    """Параметры подключения к Renovatio API."""

    base_url: str
    api_key: str
    api_version: str
    timeout_seconds: float
    seed_patient_ids: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "RenovatioSettings":
        """Читает настройки Renovatio из переменных окружения.

        SLD_RENOVATIO_BASE_URL должен указывать на общий API endpoint
        без имени метода, например: https://app.rnova.org/api/public.
        """

        patient_ids = tuple(filter(None, [item.strip() for item in os.getenv("SLD_RENOVATIO_PATIENT_IDS", "").split(",")]))
        return cls(
            base_url=os.getenv("SLD_RENOVATIO_BASE_URL", "https://app.rnova.org/api/public"),
            api_key=os.getenv("SLD_RENOVATIO_API_KEY", ""),
            api_version=os.getenv("SLD_RENOVATIO_API_VERSION", "1"),
            timeout_seconds=float(os.getenv("SLD_RENOVATIO_TIMEOUT_SECONDS", "10")),
            seed_patient_ids=patient_ids,
        )

    def validate_for_mode(self, integration_mode: str, environment: str) -> None:
        """Проверяет обязательные поля для real-режима в prod окружении."""

        if integration_mode == "real" and environment == "prod" and not self.api_key.strip():
            raise ValueError("SLD_RENOVATIO_API_KEY обязателен для real режима в prod")


@dataclass(frozen=True, slots=True)
class MaxSettings:
    """Параметры транспортной интеграции MAX."""

    base_url: str
    bot_token: str
    timeout_seconds: float
    bot_name: str
    patient_recipient_map: dict[str, str]

    @classmethod
    def from_env(cls) -> "MaxSettings":
        return cls(
            base_url=os.getenv("SLD_MAX_BASE_URL", "https://platform-api.max.ru"),
            bot_token=os.getenv("SLD_MAX_BOT_TOKEN", ""),
            timeout_seconds=float(os.getenv("SLD_MAX_TIMEOUT_SECONDS", "5")),
            bot_name=os.getenv("SLD_MAX_BOT_NAME", ""),
            patient_recipient_map=_parse_mapping(os.getenv("SLD_MAX_PATIENT_RECIPIENT_MAP", "")),
        )

    def validate_for_mode(self, integration_mode: str, environment: str) -> None:
        """Проверяет обязательные поля для real-режима в prod окружении."""

        if integration_mode == "real" and environment == "prod" and not self.bot_token.strip():
            raise ValueError("SLD_MAX_BOT_TOKEN обязателен для real режима в prod")


@dataclass(frozen=True, slots=True)
class EmailSettings:
    """Параметры SMTP-адаптера для email-доставки."""

    smtp_host: str
    smtp_port: int
    username: str
    password: str
    from_address: str
    use_tls: bool
    timeout_seconds: float

    @classmethod
    def from_env(cls) -> "EmailSettings":
        return cls(
            smtp_host=os.getenv("SLD_EMAIL_SMTP_HOST", "localhost"),
            smtp_port=int(os.getenv("SLD_EMAIL_SMTP_PORT", "25")),
            username=os.getenv("SLD_EMAIL_USERNAME", ""),
            password=os.getenv("SLD_EMAIL_PASSWORD", ""),
            from_address=os.getenv("SLD_EMAIL_FROM", "no-reply@smart-lab.local"),
            use_tls=os.getenv("SLD_EMAIL_USE_TLS", "0") == "1",
            timeout_seconds=float(os.getenv("SLD_EMAIL_TIMEOUT_SECONDS", "10")),
        )

    def validate_for_mode(self, integration_mode: str, environment: str) -> None:
        """Проверяет обязательные поля для real-режима в prod окружении."""

        if integration_mode == "real" and environment == "prod" and not self.smtp_host.strip():
            raise ValueError("SLD_EMAIL_SMTP_HOST обязателен для real режима в prod")


def _parse_mapping(raw_value: str) -> dict[str, str]:
    """Парсит отображение patient_id->recipient_id из строки `a:b,c:d`."""

    mapping: dict[str, str] = {}
    if not raw_value.strip():
        return mapping

    for pair in raw_value.split(","):
        item = pair.strip()
        if not item:
            continue
        patient_id, _, recipient_id = item.partition(":")
        if patient_id.strip() and recipient_id.strip():
            mapping[patient_id.strip()] = recipient_id.strip()
    return mapping
