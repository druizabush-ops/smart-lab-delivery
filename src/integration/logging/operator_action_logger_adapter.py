"""Инфраструктурный логер операторских команд."""

import logging

from src.application.interfaces import OperatorActionLogger
from src.infrastructure.persistence.repositories import OperatorActionAuditRepository


class OperatorActionLoggerAdapter(OperatorActionLogger):
    """Пишет аудит операторских действий в structured logging и persistence."""

    def __init__(self, audit_repository: OperatorActionAuditRepository | None = None) -> None:
        self._audit_repository = audit_repository
        self._logger = logging.getLogger("sld.operator.audit")

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
        self._logger.info(
            "operator_action",
            extra={
                "command": command,
                "card_id": card_id,
                "success": success,
                "reason": reason,
                "actor": actor,
                "source": source,
                "error": error,
            },
        )
        if self._audit_repository is None:
            return
        self._audit_repository.save(
            command=command,
            card_id=card_id,
            success=success,
            message=message,
            reason=reason,
            actor=actor,
            source=source,
            error=error,
        )
