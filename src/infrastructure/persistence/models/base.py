"""Базовый declarative класс ORM-моделей persistence слоя."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """База для таблиц persistence слоя."""
