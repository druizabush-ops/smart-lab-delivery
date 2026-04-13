"""PostgreSQL реализация контракта DeliveryCardRepository."""

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker, selectinload

from src.application.interfaces import DeliveryCardRepository
from src.domain.entities import DeliveryCard
from src.domain.statuses import QueueStatus
from src.infrastructure.identity import build_operational_card_id
from src.infrastructure.persistence.mappers import DeliveryCardMapper
from src.infrastructure.persistence.models import DeliveryCardModel


class PostgresDeliveryCardRepository(DeliveryCardRepository):
    """Репозиторий карточек доставки поверх SQLAlchemy + PostgreSQL."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save(self, card: DeliveryCard) -> None:
        card_id = build_operational_card_id(card)
        with self._session_factory() as session:
            existing = self._get_model(session, card_id)
            if existing is None:
                session.add(DeliveryCardMapper.to_model(card_id=card_id, card=card))
            else:
                DeliveryCardMapper.update_model(existing, card)
            session.commit()

    def update(self, card: DeliveryCard) -> None:
        self.save(card)

    def get_by_id(self, card_id: str) -> DeliveryCard | None:
        with self._session_factory() as session:
            model = self._get_model(session, card_id)
            if model is None:
                return None
            return DeliveryCardMapper.to_domain(model)

    def list_all(self) -> list[DeliveryCard]:
        with self._session_factory() as session:
            stmt = select(DeliveryCardModel).options(selectinload(DeliveryCardModel.attempts))
            models = session.execute(stmt).scalars().all()
            return [DeliveryCardMapper.to_domain(model) for model in models]

    def list_by_queue_status(self, status: QueueStatus) -> list[DeliveryCard]:
        with self._session_factory() as session:
            stmt = (
                select(DeliveryCardModel)
                .where(DeliveryCardModel.queue_status == status.value)
                .options(selectinload(DeliveryCardModel.attempts))
            )
            models = session.execute(stmt).scalars().all()
            return [DeliveryCardMapper.to_domain(model) for model in models]

    @staticmethod
    def _get_model(session: Session, card_id: str) -> DeliveryCardModel | None:
        stmt = (
            select(DeliveryCardModel)
            .where(DeliveryCardModel.card_id == card_id)
            .options(selectinload(DeliveryCardModel.attempts))
        )
        return session.execute(stmt).scalar_one_or_none()
