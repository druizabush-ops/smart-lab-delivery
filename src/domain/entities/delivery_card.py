"""Центральная доменная сущность карточки доставки."""

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.entities.channels import DeliveryChannel
from src.domain.entities.delivery_attempt import DeliveryAttempt
from src.domain.statuses import AttemptStatus, DeliveryStatus


@dataclass(slots=True)
class DeliveryCard:
    """Карточка доставки лабораторного результата пациенту.

    Жизненный цикл:
    1) Создание в статусе NOT_STARTED.
    2) Добавление попыток отправки (append-only история attempts).
    3) Контролируемый переход статусов до финального состояния.

    Инварианты:
    - patient_id и lab_result_id обязательны.
    - status меняется только через change_status().
    - attempts меняется только через add_attempt().
    - updated_at всегда >= created_at.
    """

    patient_id: str
    lab_result_id: str
    status: DeliveryStatus
    channel: DeliveryChannel
    attempts: list[DeliveryAttempt] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        patient_id: str,
        lab_result_id: str,
        channel: DeliveryChannel,
        created_at: datetime | None = None,
    ) -> "DeliveryCard":
        """Фабрика создания карточки с обязательными бизнес-правилами."""

        now = created_at or datetime.utcnow()
        return cls(
            patient_id=patient_id,
            lab_result_id=lab_result_id,
            status=DeliveryStatus.NOT_STARTED,
            channel=channel,
            attempts=[],
            created_at=now,
            updated_at=now,
        )

    def __post_init__(self) -> None:
        if not self.patient_id.strip():
            raise ValueError("patient_id не может быть пустым.")
        if not self.lab_result_id.strip():
            raise ValueError("lab_result_id не может быть пустым.")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at не может быть раньше created_at.")

    def change_status(self, new_status: DeliveryStatus, changed_at: datetime | None = None) -> None:
        """Изменяет статус карточки только по разрешенным переходам."""

        allowed_transitions: dict[DeliveryStatus, set[DeliveryStatus]] = {
            DeliveryStatus.NOT_STARTED: {
                DeliveryStatus.MAX_SENT,
                DeliveryStatus.EMAIL_SENT,
                DeliveryStatus.FAILED,
            },
            DeliveryStatus.FAILED: {DeliveryStatus.NOT_STARTED, DeliveryStatus.EXHAUSTED},
            DeliveryStatus.MAX_SENT: set(),
            DeliveryStatus.EMAIL_SENT: set(),
            DeliveryStatus.EXHAUSTED: set(),
        }

        if new_status == self.status:
            return

        if new_status not in allowed_transitions[self.status]:
            raise ValueError(
                f"Запрещенный переход статуса доставки: {self.status} -> {new_status}."
            )

        self.status = new_status
        self.updated_at = changed_at or datetime.utcnow()

    def add_attempt(self, attempt: DeliveryAttempt, changed_at: datetime | None = None) -> None:
        """Добавляет новую попытку в историю и обновляет статус карточки.

        Ограничение: история попыток append-only, существующие попытки не изменяются.
        """

        self.attempts.append(attempt)
        if attempt.result is AttemptStatus.SUCCESS:
            success_status = (
                DeliveryStatus.MAX_SENT
                if attempt.channel is DeliveryChannel.MAX
                else DeliveryStatus.EMAIL_SENT
            )
            self.change_status(success_status, changed_at=attempt.timestamp)
        else:
            self.change_status(DeliveryStatus.FAILED, changed_at=attempt.timestamp)

        self.updated_at = changed_at or attempt.timestamp
