"""Контракт источника готовых лабораторных результатов."""

from typing import Protocol

from src.domain.entities import LabResult


class LabResultProvider(Protocol):
    """Абстракция источника данных о готовых результатах."""

    def get_ready_results(self) -> list[LabResult]:
        """Возвращает список результатов, готовых к доставке."""
