"""ORM-модель audit trail операторских команд."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class OperatorActionLogModel(Base):
    """Таблица устойчивого аудита operator command действий."""

    __tablename__ = "operator_action_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    command: Mapped[str] = mapped_column(String(64), nullable=False)
    card_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, default=datetime.utcnow)
    success: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    message: Mapped[str] = mapped_column(Text(), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    actor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error: Mapped[str | None] = mapped_column(Text(), nullable=True)
