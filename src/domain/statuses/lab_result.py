"""Статусы готовности лабораторного результата."""

from enum import StrEnum


class LabResultStatus(StrEnum):
    """Единый перечень статусов лабораторного результата."""

    PENDING = "pending"
    READY = "ready"
    MISSING_PDF = "missing_pdf"
    BLOCKED = "blocked"
