"""Статусы результата отдельной попытки отправки."""

from enum import StrEnum


class AttemptStatus(StrEnum):
    """Терминальные исходы единичной попытки доставки."""

    SUCCESS = "success"
    ERROR = "error"
