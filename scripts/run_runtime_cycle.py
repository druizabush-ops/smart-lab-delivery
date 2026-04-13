"""CLI-скрипт одного runtime-цикла доставки.

Запуск:
    python scripts/run_runtime_cycle.py
"""

from pathlib import Path
import sys

# Добавляем корень репозитория в sys.path для запуска скрипта из папки scripts.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config.container import AppContainer


def main() -> None:
    """Собирает контейнер и запускает один синхронный цикл runtime."""

    container = AppContainer()
    patients = container.build_seed_patients()
    summary = container.delivery_runtime.process_cycle(patients)

    print("=== Delivery Runtime Summary ===")
    print(f"repository_mode={container.runtime_settings.repository_mode}")
    print(f"created_cards_count={summary.created_cards_count}")
    print(f"processed_count={summary.processed_count}")
    print(f"success_count={summary.success_count}")
    print(f"failed_count={summary.failed_count}")
    print(f"manual_review_count={summary.manual_review_count}")
    print(f"exhausted_count={summary.exhausted_count}")
    print(f"retried_count={summary.retried_count}")


if __name__ == "__main__":
    main()
