"""Тесты launch/release env-контракта."""

import pytest

from src.config.launch_mode_validation import LaunchModeValidator


def test_dev_profile_allows_in_memory_with_warning(monkeypatch) -> None:
    monkeypatch.delenv("SLD_REPOSITORY_MODE", raising=False)
    result = LaunchModeValidator().validate("dev")

    assert result.ok is True
    assert any("in_memory" in warning for warning in result.warnings)


def test_prod_profile_requires_critical_env(monkeypatch) -> None:
    monkeypatch.setenv("SLD_REPOSITORY_MODE", "postgres")
    monkeypatch.setenv("SLD_INTEGRATION_MODE", "real")
    monkeypatch.setenv("SLD_PATIENT_SECURITY_MODE", "strict")

    for key in (
        "SLD_DATABASE_URL",
        "SLD_RENOVATIO_API_KEY",
        "SLD_MAX_BOT_TOKEN",
        "SLD_MAX_BOT_NAME",
        "SLD_EMAIL_SMTP_HOST",
        "SLD_EMAIL_FROM",
        "SLD_MAX_WEBAPP_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)

    result = LaunchModeValidator().validate("prod")

    assert result.ok is False
    assert any("SLD_DATABASE_URL" in message for message in result.errors)
    assert any("SLD_MAX_BOT_TOKEN" in message for message in result.errors)


def test_prod_profile_rejects_unsafe_defaults(monkeypatch) -> None:
    monkeypatch.setenv("SLD_REPOSITORY_MODE", "postgres")
    monkeypatch.setenv("SLD_INTEGRATION_MODE", "real")
    monkeypatch.setenv("SLD_PATIENT_SECURITY_MODE", "strict")
    monkeypatch.setenv("SLD_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/smart_lab_delivery")
    monkeypatch.setenv("SLD_RENOVATIO_API_KEY", "secure")
    monkeypatch.setenv("SLD_MAX_BOT_TOKEN", "token")
    monkeypatch.setenv("SLD_MAX_BOT_NAME", "bot")
    monkeypatch.setenv("SLD_EMAIL_SMTP_HOST", "localhost")
    monkeypatch.setenv("SLD_EMAIL_FROM", "ops@example.org")
    monkeypatch.setenv("SLD_MAX_WEBAPP_SECRET", "secret")

    result = LaunchModeValidator().validate("staging")

    assert result.ok is False
    assert any("postgres:postgres" in message for message in result.errors)
    assert any("localhost" in message for message in result.errors)


def test_unknown_profile_raises_error() -> None:
    with pytest.raises(ValueError):
        LaunchModeValidator().validate("qa")
