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
        reason: str | None = None,
        actor: str | None = None,
        source: str | None = None,
        error: str | None = None,
    ) -> None:
        """Фиксирует факт вызова команды и ее результат."""
