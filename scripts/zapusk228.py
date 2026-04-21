"""Единый административный entrypoint ZAPUSK228.

Инструмент агрегирует типовой operational workflow:
- обновление кода;
- обновление зависимостей;
- миграции;
- frontend build;
- перезапуск сервисов;
- smoke checks;
- запуск тестов.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MINIAPP_DIR = PROJECT_ROOT / "frontend" / "miniapp"


@dataclass(slots=True)
class CommandRunner:
    """Обертка над выполнением shell-команд с поддержкой dry-run."""

    dry_run: bool = False

    def run(self, command: list[str], *, cwd: Path | None = None, check: bool = True) -> int:
        """Запускает команду и возвращает код завершения."""

        rendered = " ".join(shlex.quote(part) for part in command)
        location = f" (cwd={cwd})" if cwd is not None else ""
        print(f"[ZAPUSK228] $ {rendered}{location}")

        if self.dry_run:
            return 0

        completed = subprocess.run(command, cwd=cwd, check=False)
        if check and completed.returncode != 0:
            raise RuntimeError(f"Команда завершилась с rc={completed.returncode}: {rendered}")
        return completed.returncode


@dataclass(slots=True)
class Zapusk228Config:
    """Конфигурация шагов ZAPUSK228."""

    update_code: bool
    install_deps: bool
    run_migrations: bool
    rebuild_frontend: bool
    restart_services: bool
    run_smoke: bool
    run_tests: bool
    assume_yes: bool
    dry_run: bool


class Zapusk228:
    """Основной orchestrator административного цикла."""

    def __init__(
        self,
        config: Zapusk228Config,
        runner: CommandRunner,
        *,
        input_fn: Callable[[str], str] = input,
    ) -> None:
        self.config = config
        self.runner = runner
        self.input_fn = input_fn

    def execute(self) -> None:
        """Выполняет выбранные шаги в безопасной последовательности."""

        if self.config.update_code and self._confirm_step("Обновить код из origin/main?"):
            self.update_code()

        if self.config.install_deps and self._confirm_step("Обновить backend/frontend зависимости?"):
            self.install_dependencies()

        self.load_admin_env_hint()

        if self.config.run_migrations and self._confirm_step("Прогнать alembic upgrade head?"):
            self.run_migrations()

        if self.config.rebuild_frontend and self._confirm_step("Пересобрать frontend mini app?"):
            self.rebuild_frontend()

        if self.config.restart_services and self._confirm_step("Перезапустить systemd сервисы проекта?"):
            self.restart_services()

        if self.config.run_smoke and self._confirm_step("Выполнить smoke checks (health + systemd)?"):
            self.run_smoke_checks()

        if self.config.run_tests and self._confirm_step("Запустить backend тесты?"):
            self.run_backend_tests()

        print("[ZAPUSK228] Готово.")

    def update_code(self) -> None:
        """Подтягивает main-ветку из origin."""

        self.runner.run(["git", "fetch", "origin"], cwd=PROJECT_ROOT)
        self.runner.run(["git", "checkout", "main"], cwd=PROJECT_ROOT)
        self.runner.run(["git", "pull", "origin", "main"], cwd=PROJECT_ROOT)

    def install_dependencies(self) -> None:
        """Устанавливает backend и frontend зависимости."""

        self.runner.run(["python", "-m", "pip", "install", "-r", "requirements.txt"], cwd=PROJECT_ROOT)
        if MINIAPP_DIR.exists():
            self.runner.run(["npm", "install", "--no-audit", "--no-fund"], cwd=MINIAPP_DIR)

    def load_admin_env_hint(self) -> None:
        """Печатает напоминание о корректной загрузке env без утечки секретов."""

        required = [
            "SLD_ENV",
            "SLD_REPOSITORY_MODE",
            "SLD_INTEGRATION_MODE",
            "SLD_DATABASE_URL",
        ]
        print("[ZAPUSK228] Проверка env-контекста (значения скрыты):")
        for key in required:
            print(f"  - {key}: {'установлен' if os.getenv(key) else 'отсутствует'}")

    def run_migrations(self) -> None:
        """Применяет миграции БД."""

        self.runner.run(["python", "-m", "alembic", "upgrade", "head"], cwd=PROJECT_ROOT)

    def rebuild_frontend(self) -> None:
        """Собирает mini app и при наличии прав публикует dist в /var/www/miniapp."""

        if not MINIAPP_DIR.exists():
            print("[ZAPUSK228] frontend/miniapp не найден, сборка пропущена.")
            return
        self.runner.run(["npm", "run", "build"], cwd=MINIAPP_DIR)

        dist_dir = MINIAPP_DIR / "dist"
        if dist_dir.exists() and os.access("/var/www/miniapp", os.W_OK):
            self.runner.run(["cp", "-r", f"{dist_dir}/.", "/var/www/miniapp/"])
        else:
            print("[ZAPUSK228] Публикация в /var/www/miniapp пропущена (нет прав или нет dist).")

    def restart_services(self) -> None:
        """Перезапускает ключевые сервисы в рекомендуемом порядке."""

        services = [
            "smart-patient-api",
            "smart-operator-api",
            "smart-process-manager",
            "nginx",
        ]
        for service in services:
            self.runner.run(["systemctl", "restart", service])

    def run_smoke_checks(self) -> None:
        """Выполняет health и systemd smoke-проверки."""

        self.runner.run(["curl", "-fsS", "http://127.0.0.1:8001/health/live"])
        self.runner.run(["curl", "-fsS", "http://127.0.0.1:8001/health/ready"])
        self.runner.run(["curl", "-fsS", "http://127.0.0.1:8002/health/live"])
        self.runner.run(["curl", "-fsS", "http://127.0.0.1:8002/health/ready"])
        for service in ["smart-patient-api", "smart-operator-api", "smart-process-manager", "nginx"]:
            self.runner.run(["systemctl", "status", service, "--no-pager"])

    def run_backend_tests(self) -> None:
        """Запускает backend pytest suite."""

        self.runner.run(["python", "-m", "pytest"], cwd=PROJECT_ROOT)

    def _confirm_step(self, prompt: str) -> bool:
        if self.config.assume_yes:
            return True
        answer = self.input_fn(f"[ZAPUSK228] {prompt} [y/N]: ").strip().lower()
        return answer in {"y", "yes", "д", "да"}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ZAPUSK228: единый административный инструмент Smart Lab Delivery")
    parser.add_argument("--assume-yes", action="store_true", help="не задавать интерактивные подтверждения")
    parser.add_argument("--dry-run", action="store_true", help="показать шаги без выполнения команд")
    parser.add_argument("--skip-update", action="store_true", help="пропустить git update")
    parser.add_argument("--skip-deps", action="store_true", help="пропустить установку зависимостей")
    parser.add_argument("--skip-migrations", action="store_true", help="пропустить миграции")
    parser.add_argument("--skip-frontend", action="store_true", help="пропустить frontend build")
    parser.add_argument("--skip-restart", action="store_true", help="пропустить restart сервисов")
    parser.add_argument("--skip-smoke", action="store_true", help="пропустить smoke checks")
    parser.add_argument("--skip-tests", action="store_true", help="пропустить backend tests")
    return parser


def main() -> int:
    """CLI entrypoint ZAPUSK228."""

    args = _build_parser().parse_args()
    config = Zapusk228Config(
        update_code=not args.skip_update,
        install_deps=not args.skip_deps,
        run_migrations=not args.skip_migrations,
        rebuild_frontend=not args.skip_frontend,
        restart_services=not args.skip_restart,
        run_smoke=not args.skip_smoke,
        run_tests=not args.skip_tests,
        assume_yes=args.assume_yes,
        dry_run=args.dry_run,
    )
    runner = CommandRunner(dry_run=config.dry_run)
    zapusk = Zapusk228(config=config, runner=runner)
    zapusk.execute()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
