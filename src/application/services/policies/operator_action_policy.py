"""Централизованные правила допустимости операторских command-действий."""

from dataclasses import dataclass

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

    def can_retry(self, status: DeliveryStatus, queue_status: QueueStatus) -> OperatorActionDecision:
        """Retry допустим только для не-терминальных карточек и без manual review."""

        if status in self._terminal_delivery_statuses:
            return OperatorActionDecision(False, "Retry запрещен для терминальной карточки.")
        if queue_status is QueueStatus.MANUAL_REVIEW:
            return OperatorActionDecision(False, "Retry запрещен в режиме manual_review.")
        if queue_status is QueueStatus.DONE:
            return OperatorActionDecision(False, "Retry запрещен для завершенной карточки.")
        return OperatorActionDecision(True, "Retry разрешен.")

    def can_move_to_manual_review(
        self, status: DeliveryStatus, queue_status: QueueStatus
    ) -> OperatorActionDecision:
        """В manual_review можно переводить только обрабатываемые карточки."""

        if status in self._terminal_delivery_statuses:
            return OperatorActionDecision(False, "manual_review запрещен для терминальной карточки.")
        if queue_status is QueueStatus.MANUAL_REVIEW:
            return OperatorActionDecision(False, "Карточка уже находится в manual_review.")
        if queue_status is QueueStatus.DONE:
            return OperatorActionDecision(False, "manual_review запрещен для завершенной карточки.")
        return OperatorActionDecision(True, "Перевод в manual_review разрешен.")

    def can_requeue(self, status: DeliveryStatus, queue_status: QueueStatus) -> OperatorActionDecision:
        """Requeue допустим только для manual_review или waiting_retry карточек."""

        if status in self._terminal_delivery_statuses:
            return OperatorActionDecision(False, "Requeue запрещен для терминальной карточки.")
        if queue_status not in {QueueStatus.MANUAL_REVIEW, QueueStatus.WAITING_RETRY}:
            return OperatorActionDecision(False, "Requeue разрешен только из manual_review/waiting_retry.")
        return OperatorActionDecision(True, "Requeue разрешен.")

    def can_override_channel(
        self,
        status: DeliveryStatus,
        queue_status: QueueStatus,
    ) -> OperatorActionDecision:
        """Override канала безопасен только до финального успеха/исчерпания."""

        if status in self._terminal_delivery_statuses:
            return OperatorActionDecision(False, "Override канала запрещен для терминальной карточки.")
        if queue_status is QueueStatus.DONE:
            return OperatorActionDecision(False, "Override канала запрещен для завершенной карточки.")
        return OperatorActionDecision(True, "Override канала разрешен.")
