from datetime import datetime

from src.application.services import DeduplicationPolicy, DeliveryPolicy, FallbackPolicy, RetryLimits, RetryPolicy
from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import AttemptStatus, DeliveryStatus, LabResultStatus, QueueStatus


def _new_card(channel: DeliveryChannel = DeliveryChannel.MAX) -> DeliveryCard:
    patient = Patient(id="p-1", full_name="Ivan Ivanov", email="ivan@example.com")
    result = LabResult(id="lr-1", patient_id="p-1", status=LabResultStatus.READY)
    return DeliveryCard.create(patient=patient, lab_result=result, channel=channel)


def _failed_card(channel: DeliveryChannel = DeliveryChannel.MAX) -> DeliveryCard:
    card = _new_card(channel=channel)
    card.add_attempt(DeliveryAttempt(datetime.utcnow(), channel, AttemptStatus.ERROR, "err"))
    return card


def _policy() -> DeliveryPolicy:
    return DeliveryPolicy(
        retry_policy=RetryPolicy(RetryLimits(max_total_attempts=3, max_max_attempts=2, max_email_attempts=2)),
        fallback_policy=FallbackPolicy(),
        deduplication_policy=DeduplicationPolicy(),
    )


def test_retry_policy_allows_failed_with_limits() -> None:
    decision = RetryPolicy().evaluate(_failed_card())
    assert decision.can_retry_now is True


def test_retry_policy_forbids_when_total_exhausted() -> None:
    policy = RetryPolicy(RetryLimits(max_total_attempts=1, max_max_attempts=5, max_email_attempts=5))
    card = _failed_card()

    decision = policy.evaluate(card)
    assert decision.should_mark_exhausted is True


def test_retry_policy_forbids_when_max_limit_exhausted() -> None:
    policy = RetryPolicy(RetryLimits(max_total_attempts=5, max_max_attempts=1, max_email_attempts=5))
    card = _failed_card(channel=DeliveryChannel.MAX)

    decision = policy.evaluate(card)
    assert decision.can_retry_now is False
    assert decision.reason == "max_channel_limit_reached"


def test_retry_policy_forbids_when_email_limit_exhausted() -> None:
    policy = RetryPolicy(RetryLimits(max_total_attempts=5, max_max_attempts=5, max_email_attempts=1))
    card = _failed_card(channel=DeliveryChannel.EMAIL)

    decision = policy.evaluate(card)
    assert decision.can_retry_now is False
    assert decision.should_mark_exhausted is True


def test_retry_policy_forbids_terminal_statuses() -> None:
    card = _new_card()
    card.change_status(DeliveryStatus.MAX_SENT)

    decision = RetryPolicy().evaluate(card)
    assert decision.can_retry_now is False


def test_retry_policy_forbids_manual_review() -> None:
    card = _failed_card()
    card.change_queue_status(QueueStatus.MANUAL_REVIEW)

    decision = RetryPolicy().evaluate(card)
    assert decision.can_retry_now is False
    assert decision.reason == "manual_review_required"


def test_fallback_only_after_failed() -> None:
    decision = FallbackPolicy().decide(_new_card())
    assert decision.fallback_channel is None
    assert decision.reason == "fallback_only_after_failed"


def test_fallback_max_to_email_allowed_without_email_attempts() -> None:
    decision = FallbackPolicy().decide(_failed_card(channel=DeliveryChannel.MAX))
    assert decision.fallback_channel is DeliveryChannel.EMAIL


def test_fallback_repeat_forbidden() -> None:
    card = _failed_card(channel=DeliveryChannel.MAX)
    card.attempts.append(DeliveryAttempt(datetime.utcnow(), DeliveryChannel.EMAIL, AttemptStatus.ERROR, "email err"))

    decision = FallbackPolicy().decide(card)
    assert decision.should_manual_review is True
    assert decision.reason == "repeat_fallback_forbidden"


def test_fallback_no_reverse_switch_from_email_to_max() -> None:
    decision = FallbackPolicy().decide(_failed_card(channel=DeliveryChannel.EMAIL))
    assert decision.fallback_channel is None
    assert decision.should_manual_review is True


def test_fallback_email_failure_goes_manual_review_not_ping_pong() -> None:
    policy = _policy()
    decision = policy.evaluate_after_failure(_failed_card(channel=DeliveryChannel.EMAIL))

    assert decision.should_manual_review is True
    assert decision.next_channel is None


def test_deduplication_forbids_max_sent_email_sent() -> None:
    dedup = DeduplicationPolicy()

    max_sent = _new_card()
    max_sent.change_status(DeliveryStatus.MAX_SENT)
    email_sent = _new_card(channel=DeliveryChannel.EMAIL)
    email_sent.change_status(DeliveryStatus.EMAIL_SENT)

    assert dedup.evaluate(max_sent).allow_send is False
    assert dedup.evaluate(email_sent).allow_send is False


def test_deduplication_forbids_exhausted() -> None:
    card = _new_card()
    card.change_status(DeliveryStatus.FAILED)
    card.change_status(DeliveryStatus.EXHAUSTED)

    assert DeduplicationPolicy().evaluate(card).allow_send is False


def test_deduplication_forbids_if_success_attempt_exists() -> None:
    card = _new_card()
    card.attempts.append(DeliveryAttempt(datetime.utcnow(), DeliveryChannel.MAX, AttemptStatus.SUCCESS))

    assert DeduplicationPolicy().evaluate(card).allow_send is False


def test_deduplication_allows_error_attempts_if_not_terminal() -> None:
    assert DeduplicationPolicy().evaluate(_failed_card()).allow_send is True


def test_delivery_policy_evaluate_before_send_allows_valid_case() -> None:
    assert _policy().evaluate_before_send(_new_card()).can_send is True


def test_delivery_policy_evaluate_before_send_blocks_by_dedup() -> None:
    card = _new_card()
    card.change_status(DeliveryStatus.MAX_SENT)

    decision = _policy().evaluate_before_send(card)
    assert decision.can_send is False


def test_delivery_policy_after_failure_moves_to_retry() -> None:
    decision = _policy().evaluate_after_failure(_failed_card(channel=DeliveryChannel.MAX))

    assert decision.can_send is True
    assert decision.reason in {"retry_allowed", "fallback_to_email_allowed"}


def test_delivery_policy_after_failure_returns_email_next_channel_when_fallback_allowed() -> None:
    decision = _policy().evaluate_after_failure(_failed_card(channel=DeliveryChannel.MAX))

    assert decision.next_channel is DeliveryChannel.EMAIL


def test_delivery_policy_after_failure_to_manual_review_when_fallback_forbidden() -> None:
    decision = _policy().evaluate_after_failure(_failed_card(channel=DeliveryChannel.EMAIL))

    assert decision.should_manual_review is True


def test_delivery_policy_after_failure_marks_exhausted_when_limits_exhausted() -> None:
    policy = DeliveryPolicy(
        retry_policy=RetryPolicy(RetryLimits(max_total_attempts=1, max_max_attempts=1, max_email_attempts=2)),
        fallback_policy=FallbackPolicy(),
        deduplication_policy=DeduplicationPolicy(),
    )
    decision = policy.evaluate_after_failure(_failed_card())

    assert decision.should_mark_exhausted is True
