"""Smoke-проверки финальной готовности к запуску."""

from src.config.container import AppContainer
from src.config.launch_mode_validation import LaunchModeValidator
from src.presentation.operator_api import create_operator_api_app
from src.presentation.patient_api import create_patient_api_app


def test_operator_and_patient_apps_start_together() -> None:
    container = AppContainer()
    operator_app = create_operator_api_app(container=container)
    patient_app = create_patient_api_app(container=container)

    assert operator_app.title
    assert patient_app.title


def test_launch_validator_handles_current_environment() -> None:
    container = AppContainer()
    profile = container.runtime_settings.environment

    result = LaunchModeValidator().validate(profile)

    # Для dev/test допустимы предупреждения, но не должно быть падения валидатора.
    assert isinstance(result.errors, tuple)
    assert isinstance(result.warnings, tuple)
