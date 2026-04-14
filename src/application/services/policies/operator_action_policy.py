"""Централизованные правила допустимости операторских command-действий."""

from dataclasses import dataclass

from src.domain.entities import DeliveryChannel
from src.domain.statuses import DeliveryStatus, QueueStatus


@dataclass(frozen=True, slots=True)
class OperatorActionDecision:
    """Результат проверки операторского действия."""

    allowed: bool
    reason: str


class OperatorActionPolicy:
    """Проверяет, может ли оператор выполнить конкретную команду."""

    _terminal_delivery_statuses = {
        DeliveryStatus.MAX_SENT,
        DeliveryStatus.EMAIL_SENT,
        DeliveryStatus.EXHAUSTED,
    }
    _closed_queue_statuses = {QueueStatus.DONE}
    _requeue_entry_points = {QueueStatus.MANUAL_REVIEW, QueueStatus.WAITING_RETRY}

    @classmethod
    def _is_terminal_delivery(cls, status: DeliveryStatus) -> bool:
        return status in cls._terminal_delivery_statuses

    @classmethod
    def _is_closed_queue(cls, queue_status: QueueStatus) -> bool:
        return queue_status in cls._closed_queue_statuses

    def can_retry(self, status: DeliveryStatus, queue_status: QueueStatus) -> OperatorActionDecision:
        """Retry допустим только для не-терминальных карточек и без manual review."""

        if self._is_terminal_delivery(status):
            return OperatorActionDecision(False, "Retry запрещен для терминальной карточки.")
        if queue_status is QueueStatus.MANUAL_REVIEW:
            return OperatorActionDecision(False, "Retry запрещен в режиме manual_review.")
        if self._is_closed_queue(queue_status):
            return OperatorActionDecision(False, "Retry запрещен для завершенной карточки.")
        return OperatorActionDecision(True, "Retry разрешен.")

    def can_move_to_manual_review(
        self, status: DeliveryStatus, queue_status: QueueStatus
    ) -> OperatorActionDecision:
        """В manual_review можно переводить только обрабатываемые карточки."""

        if self._is_terminal_delivery(status):
            return OperatorActionDecision(False, "manual_review запрещен для терминальной карточки.")
        if queue_status is QueueStatus.MANUAL_REVIEW:
            return OperatorActionDecision(False, "Карточка уже находится в manual_review.")
        if self._is_closed_queue(queue_status):
            return OperatorActionDecision(False, "manual_review запрещен для завершенной карточки.")
        return OperatorActionDecision(True, "Перевод в manual_review разрешен.")

    def can_requeue(self, status: DeliveryStatus, queue_status: QueueStatus) -> OperatorActionDecision:
        """Requeue допустим только для manual_review или waiting_retry карточек."""

        if self._is_terminal_delivery(status):
            return OperatorActionDecision(False, "Requeue запрещен для терминальной карточки.")
        if queue_status not in self._requeue_entry_points:
            return OperatorActionDecision(False, "Requeue разрешен только из manual_review/waiting_retry.")
        return OperatorActionDecision(True, "Requeue разрешен.")

    def can_override_channel(
        self,
        status: DeliveryStatus,
        queue_status: QueueStatus,
        *,
        current_channel: DeliveryChannel,
        requested_channel: DeliveryChannel,
    ) -> OperatorActionDecision:
        """Override канала безопасен только до финального успеха/исчерпания."""

        if current_channel == requested_channel:
            return OperatorActionDecision(False, "Override канала на тот же канал запрещен.")
        if self._is_terminal_delivery(status):
            return OperatorActionDecision(False, "Override канала запрещен для терминальной карточки.")
        if self._is_closed_queue(queue_status):
            return OperatorActionDecision(False, "Override канала запрещен для завершенной карточки.")
        return OperatorActionDecision(True, "Override канала разрешен.")
