"""Централизованный словарь статусов доменного слоя.

Модуль предоставляет типобезопасные enum-статусы для всех ключевых
доменных групп. Использование строковых литералов статусов в бизнес-логике
запрещено: импортируйте и применяйте только перечисления из этого пакета.
"""

from .attempt import AttemptStatus
from .delivery import DeliveryStatus
from .lab_result import LabResultStatus
from .queue import QueueStatus

__all__ = [
    "AttemptStatus",
    "DeliveryStatus",
    "LabResultStatus",
    "QueueStatus",
]
