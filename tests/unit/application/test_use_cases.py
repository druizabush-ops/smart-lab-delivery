from datetime import datetime

from src.application.services import DeduplicationPolicy, DeliveryPolicy, FallbackPolicy, RetryLimits, RetryPolicy
from src.application.services.policies.delivery_policy import DeliveryDecision
from src.application.use_cases import (
    CreateDeliveryCardUseCase,
    HandleDeliveryFailureUseCase,
    ProcessDeliveryUseCase,
    RegisterDeliveryResultUseCase,
    RetryDeliveryUseCase,
)
from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, DeliveryStatus, LabResultStatus, QueueStatus


class StubProvider:
    def __init__(self, attempt: DeliveryAttempt) -> None:
        self.attempt = attempt
        self.calls = 0

    def send(self, card: DeliveryCard) -> DeliveryAttempt:
        self.calls += 1
        return self.attempt


class StubLogger:
    def __init__(self) -> None:
        self.logged = 0

    def log_attempt(self, card: DeliveryCard, attempt: DeliveryAttempt) -> None:
        self.logged += 1


class StubPolicy:
    def __init__(self, before: DeliveryDecision, after: DeliveryDecision) -> None:
        self.before = before
        self.after = after
        self.before_calls = 0
        self.after_calls = 0

    def evaluate_before_send(self, card: DeliveryCard) -> DeliveryDecision:
        self.before_calls += 1
        return self.before

    def evaluate_after_failure(self, card: DeliveryCard) -> DeliveryDecision:
        self.after_calls += 1
        return self.after


def _ready_data(patient_id: str = "p-1", result_id: str = "lr-1") -> tuple[Patient, LabResult]:
    patient = Patient(id=patient_id, full_name="Ivan Ivanov", email="ivan@example.com")
    result = LabResult(id=result_id, patient_id=patient_id, status=LabResultStatus.READY)
    return patient, result


def _failed_card(channel: DeliveryChannel = DeliveryChannel.MAX) -> DeliveryCard:
    patient, result = _ready_data()
    card = DeliveryCard.create(patient, result, channel)
    card.add_attempt(DeliveryAttempt(datetime.utcnow(), channel, AttemptStatus.ERROR, "err"))
    return card


def _real_policy() -> DeliveryPolicy:
    return DeliveryPolicy(
        retry_policy=RetryPolicy(RetryLimits(max_total_attempts=3, max_max_attempts=2, max_email_attempts=1)),
        fallback_policy=FallbackPolicy(),
        deduplication_policy=DeduplicationPolicy(),
    )


def test_create_delivery_card_use_case_creates_for_valid_ready_pair() -> None:
    patient, result = _ready_data()

    card = CreateDeliveryCardUseCase().execute(patient, result)

    assert card.patient_id == patient.id
    assert card.status is DeliveryStatus.NOT_STARTED


def test_create_delivery_card_use_case_delegates_validation_to_domain_factory() -> None:
    patient = Patient(id="p-1", full_name="Ivan Ivanov")
    not_ready = LabResult(id="lr-1", patient_id="p-1", status=LabResultStatus.PENDING)

    try:
        CreateDeliveryCardUseCase().execute(patient, not_ready)
        assert False, "Expected ValueError from domain factory"
    except ValueError as exc:
        assert "LabResult" in str(exc)


def test_register_delivery_result_adds_attempt_and_returns_updated_card() -> None:
    patient, result = _ready_data()
    card = DeliveryCard.create(patient, result, DeliveryChannel.MAX)
    attempt = DeliveryAttempt(datetime.utcnow(), DeliveryChannel.MAX, AttemptStatus.SUCCESS)

    updated = RegisterDeliveryResultUseCase().execute(card, attempt)

    assert updated is card
    assert len(updated.attempts) == 1
    assert updated.status is DeliveryStatus.MAX_SENT


def test_process_delivery_does_not_send_when_policy_forbids() -> None:
    patient, result = _ready_data()
    card = DeliveryCard.create(patient, result, DeliveryChannel.MAX)
    policy = StubPolicy(
        before=DeliveryDecision(False, False, False, None, "blocked"),
        after=DeliveryDecision(False, False, False, None, "unused"),
    )
    provider = StubProvider(DeliveryAttempt(datetime.utcnow(), DeliveryChannel.MAX, AttemptStatus.SUCCESS))

    use_case = ProcessDeliveryUseCase(provider, provider, policy, RegisterDeliveryResultUseCase(), HandleDeliveryFailureUseCase(_real_policy()))
    updated = use_case.execute(card)

    assert updated is card
    assert provider.calls == 0


def test_process_delivery_uses_provider_for_selected_channel() -> None:
    patient, result = _ready_data()
    card = DeliveryCard.create(patient, result, DeliveryChannel.MAX)
    policy = StubPolicy(
        before=DeliveryDecision(True, False, False, DeliveryChannel.EMAIL, "switch"),
        after=DeliveryDecision(False, False, False, None, "unused"),
    )
    max_provider = StubProvider(DeliveryAttempt(datetime.utcnow(), DeliveryChannel.MAX, AttemptStatus.SUCCESS))
    email_provider = StubProvider(DeliveryAttempt(datetime.utcnow(), DeliveryChannel.EMAIL, AttemptStatus.SUCCESS))

    use_case = ProcessDeliveryUseCase(
        max_provider,
        email_provider,
        policy,
        RegisterDeliveryResultUseCase(),
        HandleDeliveryFailureUseCase(_real_policy()),
    )
    updated = use_case.execute(card)

    assert email_provider.calls == 1
    assert max_provider.calls == 0
    assert updated.status is DeliveryStatus.EMAIL_SENT


def test_process_delivery_registers_attempt_and_handles_error_via_failure_use_case() -> None:
    patient, result = _ready_data()
    card = DeliveryCard.create(patient, result, DeliveryChannel.MAX)
    error_attempt = DeliveryAttempt(datetime.utcnow(), DeliveryChannel.MAX, AttemptStatus.ERROR, "err")
    max_provider = StubProvider(error_attempt)
    allow_policy = StubPolicy(
        before=DeliveryDecision(True, False, False, None, "allowed"),
        after=DeliveryDecision(False, True, False, None, "manual"),
    )

    use_case = ProcessDeliveryUseCase(
        max_provider,
        max_provider,
        allow_policy,
        RegisterDeliveryResultUseCase(),
        HandleDeliveryFailureUseCase(allow_policy),
        notification_logger=StubLogger(),
    )
    updated = use_case.execute(card)

    assert len(updated.attempts) == 1
    assert updated.status is DeliveryStatus.FAILED
    assert updated.queue_status is QueueStatus.MANUAL_REVIEW
    assert allow_policy.after_calls == 1


def test_handle_delivery_failure_marks_exhausted() -> None:
    card = _failed_card()
    policy = StubPolicy(
        before=DeliveryDecision(True, False, False, None, "unused"),
        after=DeliveryDecision(False, False, True, None, "exhausted"),
    )

    updated = HandleDeliveryFailureUseCase(policy).execute(card)
    assert updated.status is DeliveryStatus.EXHAUSTED


def test_handle_delivery_failure_switches_channel_from_decision() -> None:
    card = _failed_card()
    policy = StubPolicy(
        before=DeliveryDecision(True, False, False, None, "unused"),
        after=DeliveryDecision(True, False, False, DeliveryChannel.EMAIL, "fallback"),
    )

    updated = HandleDeliveryFailureUseCase(policy).execute(card)
    assert updated.channel is DeliveryChannel.EMAIL
    assert updated.status is DeliveryStatus.NOT_STARTED


def test_handle_delivery_failure_moves_to_manual_review() -> None:
    card = _failed_card()
    policy = StubPolicy(
        before=DeliveryDecision(True, False, False, None, "unused"),
        after=DeliveryDecision(False, True, False, None, "manual"),
    )

    updated = HandleDeliveryFailureUseCase(policy).execute(card)
    assert updated.queue_status is QueueStatus.MANUAL_REVIEW


def test_retry_delivery_does_not_retry_when_policy_forbids() -> None:
    card = _failed_card()
    policy = StubPolicy(
        before=DeliveryDecision(False, False, False, None, "blocked"),
        after=DeliveryDecision(False, False, False, None, "wait"),
    )
    provider = StubProvider(DeliveryAttempt(datetime.utcnow(), DeliveryChannel.MAX, AttemptStatus.SUCCESS))

    updated = RetryDeliveryUseCase(
        provider,
        provider,
        policy,
        RegisterDeliveryResultUseCase(),
        HandleDeliveryFailureUseCase(policy),
    ).execute(card)

    assert updated.status is DeliveryStatus.FAILED
    assert provider.calls == 0


def test_retry_delivery_runs_retry_when_allowed() -> None:
    card = _failed_card()
    after_policy = DeliveryDecision(False, False, False, None, "wait")
    policy = StubPolicy(
        before=DeliveryDecision(True, False, False, None, "allowed"),
        after=after_policy,
    )
    provider = StubProvider(DeliveryAttempt(datetime.utcnow(), DeliveryChannel.MAX, AttemptStatus.SUCCESS))

    updated = RetryDeliveryUseCase(
        provider,
        provider,
        policy,
        RegisterDeliveryResultUseCase(),
        HandleDeliveryFailureUseCase(policy),
    ).execute(card)

    assert provider.calls == 1
    assert updated.status is DeliveryStatus.MAX_SENT


def test_retry_delivery_uses_next_channel_from_policy() -> None:
    card = _failed_card()
    policy = StubPolicy(
        before=DeliveryDecision(True, False, False, DeliveryChannel.EMAIL, "switch"),
        after=DeliveryDecision(True, False, False, DeliveryChannel.EMAIL, "switch"),
    )
    max_provider = StubProvider(DeliveryAttempt(datetime.utcnow(), DeliveryChannel.MAX, AttemptStatus.SUCCESS))
    email_provider = StubProvider(DeliveryAttempt(datetime.utcnow(), DeliveryChannel.EMAIL, AttemptStatus.SUCCESS))

    updated = RetryDeliveryUseCase(
        max_provider,
        email_provider,
        policy,
        RegisterDeliveryResultUseCase(),
        HandleDeliveryFailureUseCase(policy),
    ).execute(card)

    assert email_provider.calls == 1
    assert updated.status is DeliveryStatus.EMAIL_SENT


def test_retry_delivery_error_attempt_goes_back_to_failure_handling() -> None:
    card = _failed_card()
    policy = StubPolicy(
        before=DeliveryDecision(True, False, False, None, "allowed"),
        after=DeliveryDecision(False, True, False, None, "manual"),
    )
    provider = StubProvider(DeliveryAttempt(datetime.utcnow(), DeliveryChannel.MAX, AttemptStatus.ERROR, "err"))

    updated = RetryDeliveryUseCase(
        provider,
        provider,
        policy,
        RegisterDeliveryResultUseCase(),
        HandleDeliveryFailureUseCase(policy),
    ).execute(card)

    assert updated.status is DeliveryStatus.FAILED
    assert updated.queue_status is QueueStatus.MANUAL_REVIEW
    assert policy.after_calls >= 1
