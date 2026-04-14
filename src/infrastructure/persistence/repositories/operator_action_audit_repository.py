"""Persistence-репозиторий для audit trail операторских команд."""

from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.persistence.models import OperatorActionLogModel


class OperatorActionAuditRepository:
    """Сохраняет операторские audit-события в БД."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save(
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
        with self._session_factory() as session:
            session.add(
                OperatorActionLogModel(
                    command=command,
                    card_id=card_id,
                    executed_at=datetime.utcnow(),
                    success=success,
                    message=message,
                    reason=reason,
                    actor=actor,
                    source=source,
                    error=error,
                )
            )
            session.commit()
