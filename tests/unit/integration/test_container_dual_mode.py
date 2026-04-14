"""Тесты wiring контейнера для stub/real integration режимов."""

from src.config.container import AppContainer


def test_container_uses_stub_mode_by_default(monkeypatch) -> None:
    monkeypatch.delenv("SLD_INTEGRATION_MODE", raising=False)

    container = AppContainer()

    assert container.runtime_settings.integration_mode == "stub"
    assert container.max_delivery_provider._mode == "stub"
    assert container.email_delivery_provider._mode == "stub"
    assert container.renovatio_client._mode == "stub"


def test_container_uses_real_mode_when_env_is_set(monkeypatch) -> None:
    monkeypatch.setenv("SLD_INTEGRATION_MODE", "real")

    container = AppContainer()

    assert container.runtime_settings.integration_mode == "real"
    assert container.max_delivery_provider._mode == "real"
    assert container.email_delivery_provider._mode == "real"
    assert container.renovatio_client._mode == "real"
