"""Локальная диагностическая проверка real Renovatio API.

Запуск из корня проекта:
    python scripts/test_renovatio_real.py
"""

from pathlib import Path
import sys
from typing import Any, Callable

# Добавляем корень репозитория в sys.path для запуска скрипта из папки scripts.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config.integration_settings import RenovatioSettings
from src.integration.errors import IntegrationFailure
from src.integration.renovatio import RenovatioClient


def _print_call_header(method_name: str) -> None:
    """Печатает заголовок диагностики для вызываемого метода."""

    print(f"\n--- Проверка метода: {method_name} ---")


def _safe_call(method_name: str, operation: Callable[[], Any]) -> None:
    """Выполняет диагностический вызов и печатает контролируемый результат."""

    _print_call_header(method_name)
    try:
        data = operation()
    except IntegrationFailure as exc:
        print(f"[ОШИБКА ИНТЕГРАЦИИ] {exc}")
    except Exception as exc:  # noqa: BLE001 - диагностический скрипт должен показывать неожиданные ошибки явно.
        print(f"[НЕОЖИДАННАЯ ОШИБКА] {type(exc).__name__}: {exc}")
    else:
        print("[УСПЕХ] Ответ получен:")
        print(data)


def main() -> None:
    """Запускает серию безопасных диагностических вызовов real Renovatio API."""

    settings = RenovatioSettings.from_env()
    if not settings.seed_patient_ids:
        print(
            "SLD_RENOVATIO_PATIENT_IDS не задан; для диагностики getReadyResults будет использован patient_id='1'.",
        )
        settings = RenovatioSettings(
            base_url=settings.base_url,
            api_key=settings.api_key,
            api_version=settings.api_version,
            timeout_seconds=settings.timeout_seconds,
            seed_patient_ids=("1",),
        )

    client = RenovatioClient(mode="real", settings=settings)

    _safe_call("getPatient(patient_id='1')", lambda: client.get_patient("1"))
    _safe_call("getPatientLabResults(patient_id='1')", lambda: client.get_patient_lab_results("1"))
    _safe_call("getReadyResults()", client.get_ready_results)


if __name__ == "__main__":
    main()
