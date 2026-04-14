"""Operator command use cases для контролируемого вмешательства в карточки."""

from dataclasses import dataclass

from src.application.interfaces import DeliveryCardRepository, OperatorActionLogger
from src.application.services.policies import OperatorActionPolicy
from src.application.use_cases.retry_delivery import RetryDeliveryUseCase
from src.domain.entities import DeliveryChannel
from src.domain.statuses import DeliveryStatus, QueueStatus


class OperatorCommandError(ValueError):
    """Ошибка исполнения операторской команды."""


@dataclass(frozen=True, slots=True)
class OperatorCommandResult:
    """Стабильный результат выполнения команды для API-ответа."""

    card_id: str
    status: str
    queue_status: str
    channel: str
    message: str


class _BaseOperatorCommandUseCase:
    """Базовый класс с общей загрузкой карточки и аудитом действий."""

    command_name = "unknown"

    def __init__(
        self,
        repository: DeliveryCardRepository,
        policy: OperatorActionPolicy,
        action_logger: OperatorActionLogger | None = None,
    ) -> None:
        self._repository = repository
        self._policy = policy
        self._action_logger = action_logger

    def _load_card(self, card_id: str):
        card = self._repository.get_by_id(card_id)
        if card is None:
            raise OperatorCommandError("Карточка не найдена.")
        return card

    def _log(self, *, card_id: str, success: bool, message: str) -> None:
        if self._action_logger is None:
            return
        self._action_logger.log_action(
            command=self.command_name,
            card_id=card_id,
            success=success,
            message=message,
        )

    @staticmethod
    def _result(card_id: str, card, message: str) -> OperatorCommandResult:
        return OperatorCommandResult(
            card_id=card_id,
            status=card.status.value,
            queue_status=card.queue_status.value,
            channel=card.channel.value,
            message=message,
        )


class RetryDeliveryCardCommandUseCase(_BaseOperatorCommandUseCase):
    """Операторский retry, который использует уже существующий retry-пайплайн."""

    command_name = "retry"

    def __init__(
        self,
        repository: DeliveryCardRepository,
        policy: OperatorActionPolicy,
        retry_use_case: RetryDeliveryUseCase,
        action_logger: OperatorActionLogger | None = None,
    ) -> None:
        super().__init__(repository=repository, policy=policy, action_logger=action_logger)
        self._retry_use_case = retry_use_case

    def execute(self, card_id: str) -> OperatorCommandResult:
        card = self._load_card(card_id)
        decision = self._policy.can_retry(card.status, card.queue_status)
        if not decision.allowed:
            self._log(card_id=card_id, success=False, message=decision.reason)
            raise OperatorCommandError(decision.reason)

        updated = self._retry_use_case.execute(card)
        self._repository.update(updated)
        self._log(card_id=card_id, success=True, message="Retry выполнен.")
        return self._result(card_id, updated, "Retry выполнен.")


class MoveToManualReviewCommandUseCase(_BaseOperatorCommandUseCase):
    """Переводит карточку в manual_review в рамках разрешенных состояний."""

    command_name = "manual_review"

    def execute(self, card_id: str, reason: str | None = None) -> OperatorCommandResult:
        card = self._load_card(card_id)
        decision = self._policy.can_move_to_manual_review(card.status, card.queue_status)
        if not decision.allowed:
            self._log(card_id=card_id, success=False, message=decision.reason)
            raise OperatorCommandError(decision.reason)

        card.change_queue_status(QueueStatus.MANUAL_REVIEW)
        self._repository.update(card)
        message = "Карточка переведена в manual_review."
        if reason:
            message = f"{message} Причина: {reason}"
        self._log(card_id=card_id, success=True, message=message)
        return self._result(card_id, card, message)


class RequeueDeliveryCardCommandUseCase(_BaseOperatorCommandUseCase):
    """Возвращает карточку из manual_review/waiting_retry в активную обработку."""

    command_name = "requeue"

    def execute(self, card_id: str, reason: str | None = None) -> OperatorCommandResult:
        card = self._load_card(card_id)
        decision = self._policy.can_requeue(card.status, card.queue_status)
        if not decision.allowed:
            self._log(card_id=card_id, success=False, message=decision.reason)
            raise OperatorCommandError(decision.reason)

        if card.status is DeliveryStatus.FAILED:
            card.change_status(DeliveryStatus.NOT_STARTED)
        else:
            card.change_queue_status(QueueStatus.ACTIVE)
        self._repository.update(card)
        message = "Карточка поставлена в активную очередь."
        if reason:
            message = f"{message} Причина: {reason}"
        self._log(card_id=card_id, success=True, message=message)
        return self._result(card_id, card, message)


class OverrideChannelCommandUseCase(_BaseOperatorCommandUseCase):
    """Меняет канал доставки вручную в безопасных состояниях карточки."""

    command_name = "override_channel"

    def execute(
        self,
        card_id: str,
        *,
        channel: DeliveryChannel,
        reason: str | None = None,
    ) -> OperatorCommandResult:
        card = self._load_card(card_id)
        decision = self._policy.can_override_channel(card.status, card.queue_status)
        if not decision.allowed:
            self._log(card_id=card_id, success=False, message=decision.reason)
            raise OperatorCommandError(decision.reason)

        card.channel = channel
        self._repository.update(card)
        message = f"Канал доставки изменен на {channel.value}."
        if reason:
            message = f"{message} Причина: {reason}"
        self._log(card_id=card_id, success=True, message=message)
        return self._result(card_id, card, message)
