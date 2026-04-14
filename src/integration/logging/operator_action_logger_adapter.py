"""Инфраструктурный логер операторских команд."""

from src.application.interfaces import OperatorActionLogger


class OperatorActionLoggerAdapter(OperatorActionLogger):
    """Пишет аудит операторских действий в stdout."""

    def log_action(self, *, command: str, card_id: str, success: bool, message: str) -> None:
        print(
            "[operator-action] "
            f"command={command} "
            f"card_id={card_id} "
            f"success={success} "
            f"message={message}"
        )
