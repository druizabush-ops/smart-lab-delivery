"""ORM-модель таблицы delivery_cards."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence.models.base import Base


class DeliveryCardModel(Base):
    __tablename__ = "delivery_cards"

    card_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(255), nullable=False)
    lab_result_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    queue_status: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)

    attempts = relationship(
        "DeliveryAttemptModel",
        back_populates="card",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DeliveryAttemptModel.sequence_no",
    )
