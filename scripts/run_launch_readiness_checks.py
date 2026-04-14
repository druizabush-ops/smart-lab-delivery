"""Финальный smoke-контур go-live readiness проверок."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.config.container import AppContainer
from src.config.launch_mode_validation import LaunchModeValidator


def _run_command(name: str, command: list[str], *, cwd: Path | None = None) -> tuple[bool, str]:
    """Запускает внешнюю команду и возвращает результат для launch-репорта."""

    try:
        completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        return False, f"{name}: команда не найдена ({exc})"

    if completed.returncode != 0:
        output = (completed.stdout + "\n" + completed.stderr).strip()
        return False, f"{name}: rc={completed.returncode}\n{output}"

    return True, f"{name}: ok"


def main() -> int:
    """Выполняет launch-readiness smoke и печатает итоговый статус."""

    validator = LaunchModeValidator()
    target_profile = AppContainer().runtime_settings.environment
    validation_result = validator.validate(target_profile)

    checks: list[tuple[str, bool, str]] = []

    checks.append(("env_contract", validation_result.ok, "; ".join(validation_result.errors) or "ok"))

    container = AppContainer()
    health = container.runtime_settings
    checks.append(("runtime_settings_loaded", True, f"env={health.environment}, repo={health.repository_mode}, integration={health.integration_mode}"))

    db_ok = True
    db_details = "postgres не требуется"
    if container.runtime_settings.repository_mode == "postgres":
        from src.presentation.common.health import HealthService

        status = HealthService(container).get_readiness()
        db_ok = status.db_ok
        db_details = "db ok" if db_ok else "db check failed"
    checks.append(("db_access", db_ok, db_details))

    cmd_checks = [
        ("runtime_cycle", [sys.executable, "scripts/run_runtime_cycle.py"]),
        ("process_manager", [sys.executable, "scripts/run_process_manager.py"]),
        ("health_and_readiness_tests", [sys.executable, "-m", "pytest", "tests/integration/test_hardening_endpoints.py"]),
        ("operator_patient_parallel_tests", [sys.executable, "-m", "pytest", "tests/integration/test_operator_api_read_only.py", "tests/integration/test_patient_api_read_only.py"]),
        ("audit_tests", [sys.executable, "-m", "pytest", "tests/unit/application/test_operator_audit_logging.py"]),
        ("launch_mode_validation_tests", [sys.executable, "-m", "pytest", "tests/unit/config/test_launch_mode_validation.py"]),
    ]

    if container.runtime_settings.repository_mode == "postgres":
        ok, details = _run_command("alembic_upgrade_head", [sys.executable, "-m", "alembic", "upgrade", "head"])
        checks.append(("alembic_upgrade_head", ok, details))
    else:
        checks.append(("alembic_upgrade_head", True, "пропущено: repository_mode!=postgres"))

    for check_name, command in cmd_checks:
        ok, details = _run_command(check_name, command)
        checks.append((check_name, ok, details))

    frontend_dir = Path("frontend/miniapp")
    npm_exists = subprocess.run(["bash", "-lc", "command -v npm >/dev/null 2>&1"], check=False).returncode == 0
    if npm_exists:
        install_ok, install_details = _run_command("miniapp_install", ["npm", "install", "--no-audit", "--no-fund"], cwd=frontend_dir)
        checks.append(("miniapp_install", install_ok, install_details))
        if install_ok:
            ok, details = _run_command("miniapp_build", ["npm", "run", "build"], cwd=frontend_dir)
            checks.append(("miniapp_build", ok, details))
        else:
            checks.append(("miniapp_build", False, "пропущено: не удалось установить frontend зависимости"))
    else:
        checks.append(("miniapp_build", False, "npm не найден в окружении"))

    has_failures = False
    print("=== Launch Readiness Report ===")
    for name, ok, details in checks:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: {details}")
        if not ok:
            has_failures = True

    if validation_result.warnings:
        print("=== Launch warnings ===")
        for warning in validation_result.warnings:
            print(f"[WARN] {warning}")

    return 1 if has_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
