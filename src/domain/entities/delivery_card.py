"""Центральная доменная сущность карточки доставки."""

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.entities.channels import DeliveryChannel
from src.domain.entities.delivery_attempt import DeliveryAttempt
from src.domain.entities.lab_result import LabResult
from src.domain.entities.patient import Patient
from src.domain.statuses.lab_result import LabResultStatus
from src.domain.statuses import AttemptStatus, DeliveryStatus, QueueStatus


@dataclass(slots=True)
class DeliveryCard:
    """Карточка доставки лабораторного результата пациенту.

    Жизненный цикл:
    1) Создание в статусах NOT_STARTED/ACTIVE.
    2) Добавление попыток отправки (append-only история attempts).
    3) Контролируемый переход delivery/queue статусов до финального состояния.

    Инварианты:
    - patient_id и lab_result_id обязательны.
    - status и queue_status меняются только через доменные методы.
    - attempts меняется только через add_attempt().
    - updated_at всегда >= created_at.
    - При успешной или финально закрытой доставке queue_status обязан быть DONE.
    """

    patient_id: str
    lab_result_id: str
    status: DeliveryStatus
    queue_status: QueueStatus
    channel: DeliveryChannel
    attempts: list[DeliveryAttempt] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        patient: Patient,
        lab_result: LabResult,
        channel: DeliveryChannel,
        created_at: datetime | None = None,
    ) -> "DeliveryCard":
        """Фабрика создания карточки с обязательными бизнес-правилами."""

        if lab_result.status is not LabResultStatus.READY:
            raise ValueError("DeliveryCard можно создавать только для LabResult в статусе READY.")

        if lab_result.patient_id != patient.id:
            raise ValueError("patient.id должен совпадать с lab_result.patient_id.")

        now = created_at or datetime.utcnow()
        return cls(
            patient_id=patient.id,
            lab_result_id=lab_result.id,
            status=DeliveryStatus.NOT_STARTED,
            queue_status=QueueStatus.ACTIVE,
            channel=channel,
            attempts=[],
            created_at=now,
            updated_at=now,
        )

    def can_be_sent(self) -> bool:
        """Возвращает допустимость отправки карточки по доменным статусам."""

        if self.status in {DeliveryStatus.MAX_SENT, DeliveryStatus.EMAIL_SENT, DeliveryStatus.EXHAUSTED}:
            return False

        return self.queue_status in {QueueStatus.ACTIVE, QueueStatus.WAITING_RETRY}

    def __post_init__(self) -> None:
        if not self.patient_id.strip():
            raise ValueError("patient_id не может быть пустым.")
        if not self.lab_result_id.strip():
            raise ValueError("lab_result_id не может быть пустым.")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at не может быть раньше created_at.")

        terminal_delivery = {
            DeliveryStatus.MAX_SENT,
            DeliveryStatus.EMAIL_SENT,
            DeliveryStatus.EXHAUSTED,
        }
        if self.status in terminal_delivery and self.queue_status is not QueueStatus.DONE:
            raise ValueError("Для терминального статуса доставки queue_status должен быть DONE.")

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
        self._sync_queue_status_from_delivery(new_status)
        self.updated_at = changed_at or datetime.utcnow()

    def change_queue_status(self, new_status: QueueStatus, changed_at: datetime | None = None) -> None:
        """Изменяет операционный queue_status карточки по разрешенным переходам."""

        allowed_transitions: dict[QueueStatus, set[QueueStatus]] = {
            QueueStatus.ACTIVE: {
                QueueStatus.WAITING_RETRY,
                QueueStatus.MANUAL_REVIEW,
                QueueStatus.DONE,
            },
            QueueStatus.WAITING_RETRY: {
                QueueStatus.ACTIVE,
                QueueStatus.MANUAL_REVIEW,
                QueueStatus.DONE,
            },
            QueueStatus.MANUAL_REVIEW: {
                QueueStatus.ACTIVE,
                QueueStatus.DONE,
            },
            QueueStatus.DONE: set(),
        }

        if new_status == self.queue_status:
            return

        if new_status not in allowed_transitions[self.queue_status]:
            raise ValueError(
                f"Запрещенный переход queue_status: {self.queue_status} -> {new_status}."
            )

        self.queue_status = new_status
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

    def _sync_queue_status_from_delivery(self, delivery_status: DeliveryStatus) -> None:
        """Синхронизирует queue_status по доменному delivery_status."""

        if delivery_status in {DeliveryStatus.MAX_SENT, DeliveryStatus.EMAIL_SENT, DeliveryStatus.EXHAUSTED}:
            self.queue_status = QueueStatus.DONE
            return

        if delivery_status is DeliveryStatus.FAILED:
            self.queue_status = QueueStatus.WAITING_RETRY
            return

        if delivery_status is DeliveryStatus.NOT_STARTED and self.queue_status is not QueueStatus.MANUAL_REVIEW:
            self.queue_status = QueueStatus.ACTIVE
