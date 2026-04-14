"""Контракт инфраструктурного аудита операторских команд."""

from typing import Protocol


class OperatorActionLogger(Protocol):
    """Логирует результат выполнения операторской команды."""

    def log_action(
        self,
        *,
        command: str,
        card_id: str,
        success: bool,
        message: str,
    ) -> None:
        """Фиксирует факт вызова команды и ее результат."""
