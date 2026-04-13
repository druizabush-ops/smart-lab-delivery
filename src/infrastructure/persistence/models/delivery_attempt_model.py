"""ORM-модель таблицы delivery_attempts."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence.models.base import Base


class DeliveryAttemptModel(Base):
    __tablename__ = "delivery_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("delivery_cards.card_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    card = relationship("DeliveryCardModel", back_populates="attempts")
