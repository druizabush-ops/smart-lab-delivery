"""CLI-скрипт process manager lifecycle цикла.

Запуск:
    python scripts/run_process_manager.py
"""

from pathlib import Path
import sys

# Добавляем корень репозитория в sys.path для запуска скрипта из папки scripts.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config.container import AppContainer


def main() -> None:
    """Собирает контейнер и выполняет управляемый lifecycle run_all_pending."""

    container = AppContainer()
    patients = container.build_seed_patients()
    summary = container.delivery_process_manager.run_all_pending(patients)

    print("=== Delivery Process Manager Summary ===")
    print(f"repository_mode={container.runtime_settings.repository_mode}")
    print(f"new_cards_discovered={summary.new_cards_discovered}")
    print(f"existing_cards_reprocessed={summary.existing_cards_reprocessed}")
    print(f"retry_candidates_count={summary.retry_candidates_count}")
    print(f"processed_count={summary.processed_count}")
    print(f"success_count={summary.success_count}")
    print(f"failed_count={summary.failed_count}")
    print(f"manual_review_count={summary.manual_review_count}")
    print(f"exhausted_count={summary.exhausted_count}")


if __name__ == "__main__":
    main()
