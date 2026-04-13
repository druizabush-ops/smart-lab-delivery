"""SQLAlchemy engine/session фабрики для persistence слоя."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.persistence.settings import DatabaseSettings


def build_engine(settings: DatabaseSettings):
    return create_engine(settings.url, future=True)


def build_session_factory(settings: DatabaseSettings) -> sessionmaker[Session]:
    engine = build_engine(settings)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
