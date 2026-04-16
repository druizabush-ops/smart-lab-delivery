"""Локальная диагностика patient-facing auth flow для Renovatio.

Запуск из корня проекта:
    python scripts/test_renovatio_patient_auth_flow.py
"""

from pathlib import Path
import sys
from typing import Any

# Добавляем корень репозитория в sys.path для запуска скрипта из папки scripts.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config.integration_settings import RenovatioSettings
from src.integration.errors import IntegrationFailure
from src.integration.renovatio import RenovatioClient


def _print_step(title: str) -> None:
    """Печатает текущий шаг диагностики."""

    print(f"\n=== {title} ===")


def _safe_call(title: str, operation: Any) -> Any:
    """Выполняет шаг с контролируемой обработкой интеграционных ошибок."""

    _print_step(title)
    try:
        response = operation()
    except IntegrationFailure as exc:
        print(f"[ОШИБКА ИНТЕГРАЦИИ] {exc}")
        return None
    except Exception as exc:  # noqa: BLE001 - диагностический entrypoint должен явно показывать неожиданные ошибки.
        print(f"[НЕОЖИДАННАЯ ОШИБКА] {type(exc).__name__}: {exc}")
        return None

    print("[УСПЕХ] Ответ получен:")
    print(response)
    return response


def _ask_auth_payload() -> dict[str, str]:
    """Собирает входные данные для authPatient без хранения секретов в коде."""

    _print_step("Шаг A: authPatient")
    print("Выберите вариант авторизации: ")
    print("  1) По телефону")
    print("  2) По login/password")
    choice = input("Введите 1 или 2 (по умолчанию 1): ").strip() or "1"

    if choice == "2":
        login = input("Введите login: ").strip()
        password = input("Введите password: ").strip()
        if not login or not password:
            raise ValueError("Для login/password авторизации оба поля обязательны.")
        return {"login": login, "password": password}

    phone = input("Введите phone (например, +79990000000): ").strip()
    if not phone:
        raise ValueError("Для авторизации по телефону поле phone обязательно.")
    return {"phone": phone}


def _extract_patient_key(auth_response: dict[str, Any], client: RenovatioClient) -> str | None:
    """Извлекает patient_key напрямую или через checkAuthCode при 2FA."""

    direct_key = str(auth_response.get("patient_key") or "").strip()
    if direct_key:
        _print_step("Шаг B: patient_key получен из authPatient")
        print("[УСПЕХ] patient_key получен без checkAuthCode.")
        return direct_key

    patient_id = str(auth_response.get("patient_id") or "").strip()
    need_auth_key = auth_response.get("need_auth_key")
    if not patient_id or not need_auth_key:
        print("[ВНИМАНИЕ] authPatient не вернул patient_key и не потребовал auth_code.")
        return None

    _print_step("Шаг C: требуется checkAuthCode")
    auth_code = input("Введите auth_code из SMS/почты: ").strip()
    if not auth_code:
        print("[ОСТАНОВКА] auth_code не введен, сценарий прерван.")
        return None

    check_response = _safe_call(
        "checkAuthCode",
        lambda: client.check_auth_code(patient_id=patient_id, auth_code=auth_code),
    )
    if not isinstance(check_response, dict):
        return None

    checked_key = str(check_response.get("patient_key") or "").strip()
    if not checked_key:
        print("[ОШИБКА] checkAuthCode не вернул patient_key.")
        return None
    return checked_key


def main() -> None:
    """Запускает ручной диагностический сценарий patient auth flow."""

    settings = RenovatioSettings.from_env()
    client = RenovatioClient(mode="real", settings=settings)

    print("Диагностика patient auth flow Renovatio (локальный сценарий).")
    print("Требуется задать env SLD_RENOVATIO_BASE_URL и SLD_RENOVATIO_API_KEY.")

    try:
        auth_payload = _ask_auth_payload()
    except ValueError as exc:
        print(f"[ОШИБКА ВВОДА] {exc}")
        return

    auth_response = _safe_call("authPatient", lambda: client.auth_patient(**auth_payload))
    if not isinstance(auth_response, dict):
        return

    patient_key = _extract_patient_key(auth_response, client)
    if not patient_key:
        return

    _print_step("Шаг D: проверка patient-facing методов")
    info = _safe_call("getPatientInfo", lambda: client.get_patient_info(patient_key))
    if info is None:
        return

    results = _safe_call(
        "getPatientLabResults",
        lambda: client.get_patient_lab_results_by_key(patient_key),
    )
    if not isinstance(results, list) or not results:
        print("[ЗАВЕРШЕНО] Список результатов пуст, getPatientLabResultDetails не вызывается.")
        return

    first_result = results[0] if isinstance(results[0], dict) else {}
    result_id = str(first_result.get("id") or first_result.get("result_id") or "").strip()
    if not result_id:
        print("[ЗАВЕРШЕНО] В первом результате нет id/result_id для детализации.")
        return

    _safe_call(
        "getPatientLabResultDetails",
        lambda: client.get_patient_lab_result_details_by_key(patient_key, result_id),
    )


if __name__ == "__main__":
    main()
