"""Доменная сущность пациента, получающего лабораторный результат."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Patient:
    """Пациент клиники.

    Инварианты:
    - Идентификатор пациента не пустой.
    - Для контактного email допускается пустое значение,
      но если email задан, он должен содержать символ '@'.
    """

    id: str
    full_name: str
    email: str | None = None
    phone: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Идентификатор пациента не может быть пустым.")
        if not self.full_name.strip():
            raise ValueError("ФИО пациента не может быть пустым.")
        if self.email and "@" not in self.email:
            raise ValueError("Email пациента должен содержать символ '@'.")
