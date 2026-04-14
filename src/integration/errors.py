"""Централизованные типы ошибок интеграционного слоя."""

from dataclasses import dataclass
from enum import Enum


class IntegrationErrorKind(str, Enum):
    """Категории сбоев внешних интеграций."""

    TIMEOUT = "timeout"
    AUTH = "auth_failure"
    BAD_RESPONSE = "bad_response"
    EMPTY_RESULT = "empty_result"
    DELIVERY_MAX = "max_delivery_failure"
    DELIVERY_EMAIL = "email_delivery_failure"
    CONFIG = "integration_config_error"


@dataclass(frozen=True, slots=True)
class IntegrationFailure(Exception):
    """Структурированный сбой интеграции для централизованного mapping."""

    kind: IntegrationErrorKind
    message: str

    def __str__(self) -> str:
        return f"[{self.kind}] {self.message}"
