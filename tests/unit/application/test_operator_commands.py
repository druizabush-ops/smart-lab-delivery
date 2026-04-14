from datetime import datetime

from src.application.services.policies import OperatorActionPolicy
from src.application.use_cases.operator_commands import (
    MoveToManualReviewCommandUseCase,
    OperatorCommandError,
    OverrideChannelCommandUseCase,
    RequeueDeliveryCardCommandUseCase,
    RetryDeliveryCardCommandUseCase,
)
from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, DeliveryStatus, LabResultStatus, QueueStatus
from src.infrastructure.identity import build_operational_card_id
from src.infrastructure.repositories import InMemoryDeliveryCardRepository


class StubRetryUseCase:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, card: DeliveryCard) -> DeliveryCard:
        self.calls += 1
        card.change_status(DeliveryStatus.NOT_STARTED)
        card.change_queue_status(QueueStatus.ACTIVE)
        return card


def _build_card() -> DeliveryCard:
    patient = Patient(id="p-1", full_name="Operator Test", email="operator@example.org")
    result = LabResult(id="lr-1", patient_id="p-1", status=LabResultStatus.READY)
    return DeliveryCard.create(patient=patient, lab_result=result, channel=DeliveryChannel.MAX)


def test_operator_action_policy_blocks_terminal_commands() -> None:
    policy = OperatorActionPolicy()

    retry_decision = policy.can_retry(DeliveryStatus.MAX_SENT, QueueStatus.DONE)
    requeue_decision = policy.can_requeue(DeliveryStatus.EXHAUSTED, QueueStatus.DONE)
    override_decision = policy.can_override_channel(
        DeliveryStatus.EMAIL_SENT,
        QueueStatus.DONE,
        current_channel=DeliveryChannel.MAX,
        requested_channel=DeliveryChannel.EMAIL,
    )

    assert not retry_decision.allowed
    assert not requeue_decision.allowed
    assert not override_decision.allowed


def test_retry_command_runs_for_allowed_state() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card()
    card.add_attempt(
        DeliveryAttempt(
            timestamp=datetime.utcnow(),
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.ERROR,
            error_message="network",
        )
    )
    card_id = build_operational_card_id(card)
    repository.save(card)

    retry_stub = StubRetryUseCase()
    use_case = RetryDeliveryCardCommandUseCase(repository, OperatorActionPolicy(), retry_stub)
    result = use_case.execute(card_id)

    assert retry_stub.calls == 1
    assert result.queue_status == QueueStatus.ACTIVE.value


def test_retry_command_rejects_manual_review_state() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card()
    card.change_queue_status(QueueStatus.MANUAL_REVIEW)
    card_id = build_operational_card_id(card)
    repository.save(card)

    use_case = RetryDeliveryCardCommandUseCase(repository, OperatorActionPolicy(), StubRetryUseCase())

    try:
        use_case.execute(card_id)
        assert False, "Ожидался OperatorCommandError"
    except OperatorCommandError as exc:
        assert "manual_review" in str(exc)


def test_retry_command_rejects_terminal_state() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card()
    card.add_attempt(
        DeliveryAttempt(
            timestamp=datetime.utcnow(),
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.SUCCESS,
        )
    )
    card_id = build_operational_card_id(card)
    repository.save(card)

    use_case = RetryDeliveryCardCommandUseCase(repository, OperatorActionPolicy(), StubRetryUseCase())

    try:
        use_case.execute(card_id)
        assert False, "Ожидался OperatorCommandError"
    except OperatorCommandError as exc:
        assert "терминальной" in str(exc)


def test_manual_review_command_moves_card() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card()
    card_id = build_operational_card_id(card)
    repository.save(card)

    result = MoveToManualReviewCommandUseCase(repository, OperatorActionPolicy()).execute(card_id, reason="ручная проверка")

    assert result.queue_status == QueueStatus.MANUAL_REVIEW.value
    assert "Причина" in result.message


def test_requeue_command_returns_card_to_active() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card()
    card.change_queue_status(QueueStatus.MANUAL_REVIEW)
    card_id = build_operational_card_id(card)
    repository.save(card)

    result = RequeueDeliveryCardCommandUseCase(repository, OperatorActionPolicy()).execute(card_id)

    assert result.queue_status == QueueStatus.ACTIVE.value


def test_requeue_from_manual_review_with_failed_status_resets_for_next_cycle() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card()
    card.add_attempt(
        DeliveryAttempt(
            timestamp=datetime.utcnow(),
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.ERROR,
            error_message="network",
        )
    )
    card.change_queue_status(QueueStatus.MANUAL_REVIEW)
    card_id = build_operational_card_id(card)
    repository.save(card)

    result = RequeueDeliveryCardCommandUseCase(repository, OperatorActionPolicy()).execute(card_id)

    assert result.status == DeliveryStatus.NOT_STARTED.value
    assert result.queue_status == QueueStatus.ACTIVE.value


def test_requeue_command_rejects_non_requeue_state() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card()
    card_id = build_operational_card_id(card)
    repository.save(card)

    use_case = RequeueDeliveryCardCommandUseCase(repository, OperatorActionPolicy())
    try:
        use_case.execute(card_id)
        assert False, "Ожидался OperatorCommandError"
    except OperatorCommandError as exc:
        assert "manual_review/waiting_retry" in str(exc)


def test_override_channel_command_updates_channel() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card()
    card_id = build_operational_card_id(card)
    repository.save(card)

    result = OverrideChannelCommandUseCase(repository, OperatorActionPolicy()).execute(
        card_id,
        channel=DeliveryChannel.EMAIL,
        reason="MAX недоступен",
    )

    assert result.channel == DeliveryChannel.EMAIL.value


def test_override_channel_command_rejects_same_channel() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card()
    card_id = build_operational_card_id(card)
    repository.save(card)

    use_case = OverrideChannelCommandUseCase(repository, OperatorActionPolicy())
    try:
        use_case.execute(card_id, channel=DeliveryChannel.MAX)
        assert False, "Ожидался OperatorCommandError"
    except OperatorCommandError as exc:
        assert "тот же канал" in str(exc)


def test_override_channel_command_rejects_terminal_card() -> None:
    repository = InMemoryDeliveryCardRepository()
    card = _build_card()
    card.add_attempt(
        DeliveryAttempt(
            timestamp=datetime.utcnow(),
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.SUCCESS,
        )
    )
    card_id = build_operational_card_id(card)
    repository.save(card)

    use_case = OverrideChannelCommandUseCase(repository, OperatorActionPolicy())
    try:
        use_case.execute(card_id, channel=DeliveryChannel.EMAIL)
        assert False, "Ожидался OperatorCommandError"
    except OperatorCommandError as exc:
        assert "терминальной" in str(exc)
