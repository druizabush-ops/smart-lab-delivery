"""Статусы отдельной попытки отправки."""

from enum import StrEnum


class AttemptStatus(StrEnum):
    """Единый перечень статусов жизненного цикла попытки."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"
