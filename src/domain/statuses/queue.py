"""Статусы карточки в очереди обработки."""

from enum import StrEnum


class QueueStatus(StrEnum):
    """Единый перечень операционных статусов очереди."""

    ACTIVE = "active"
    WAITING_RETRY = "waiting_retry"
    MANUAL_REVIEW = "manual_review"
    DONE = "done"
