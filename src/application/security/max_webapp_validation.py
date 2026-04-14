"""Валидация MAX WebAppData/initData на сервере."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
from urllib.parse import parse_qsl


@dataclass(frozen=True, slots=True)
class MaxWebAppValidationResult:
    """Результат серверной проверки initData."""

    is_valid: bool
    reason: str | None
    user_id: str | None
    start_param: str | None


def validate_max_webapp_data(init_data: str, secret: str) -> MaxWebAppValidationResult:
    """Проверяет подпись MAX WebAppData по hash-контракту документации."""

    if not init_data.strip():
        return MaxWebAppValidationResult(False, "Пустой init_data", None, None)

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    provided_hash = pairs.pop("hash", "")
    if not provided_hash:
        return MaxWebAppValidationResult(False, "Отсутствует hash", None, pairs.get("start_param"))

    if not secret.strip():
        return MaxWebAppValidationResult(False, "Секрет проверки не настроен на сервере", None, pairs.get("start_param"))

    check_string = "\n".join(f"{key}={value}" for key, value in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", secret.encode("utf-8"), hashlib.sha256).digest()
    expected = hmac.new(secret_key, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, provided_hash):
        return MaxWebAppValidationResult(False, "Некорректная подпись init_data", None, pairs.get("start_param"))

    user_id = _extract_user_id(pairs.get("user", ""))
    return MaxWebAppValidationResult(True, None, user_id, pairs.get("start_param"))


def _extract_user_id(raw_user: str) -> str | None:
    """Извлекает user.id из сериализованного payload поля user."""

    if not raw_user.strip():
        return None
    try:
        parsed = json.loads(raw_user)
    except json.JSONDecodeError:
        return None
    user_id = parsed.get("id")
    if user_id is None:
        return None
    return str(user_id)
