"""Доменная сущность попытки доставки результата пациенту."""

from dataclasses import dataclass
from datetime import datetime

from src.domain.entities.channels import DeliveryChannel
from src.domain.statuses import AttemptStatus


@dataclass(frozen=True, slots=True)
class DeliveryAttempt:
    """Запись о единичной попытке отправки.

    Поля:
    - timestamp: время регистрации попытки.
    - channel: канал доставки (MAX/EMAIL).
    - result: итог попытки (success/fail в доменных терминах через enum).
    - error_message: текст ошибки, если попытка неуспешна.

    Инварианты:
    - Для ERROR обязателен error_message.
    - Для SUCCESS запрещен error_message.
    """

    timestamp: datetime
    channel: DeliveryChannel
    result: AttemptStatus
    error_message: str | None = None

    def __post_init__(self) -> None:
        allowed_terminal = {AttemptStatus.SUCCESS, AttemptStatus.ERROR}
        if self.result not in allowed_terminal:
            raise ValueError("result попытки должен быть SUCCESS или ERROR.")

        if self.result is AttemptStatus.ERROR and not self.error_message:
            raise ValueError("Для неуспешной попытки требуется error_message.")

        if self.result is AttemptStatus.SUCCESS and self.error_message:
            raise ValueError("Для успешной попытки error_message должен отсутствовать.")
