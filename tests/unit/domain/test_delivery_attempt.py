from datetime import datetime

from src.domain.entities import DeliveryAttempt, DeliveryChannel
from src.domain.statuses import AttemptStatus


def test_delivery_attempt_success_without_error_message() -> None:
    attempt = DeliveryAttempt(
        timestamp=datetime.utcnow(),
        channel=DeliveryChannel.MAX,
        result=AttemptStatus.SUCCESS,
    )

    assert attempt.result is AttemptStatus.SUCCESS
    assert attempt.error_message is None


def test_delivery_attempt_success_with_error_message_raises_error() -> None:
    try:
        DeliveryAttempt(
            timestamp=datetime.utcnow(),
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.SUCCESS,
            error_message="unexpected",
        )
        assert False, "Expected ValueError for SUCCESS with error_message"
    except ValueError as exc:
        assert "успешной попытки" in str(exc)


def test_delivery_attempt_error_without_error_message_raises_error() -> None:
    try:
        DeliveryAttempt(
            timestamp=datetime.utcnow(),
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.ERROR,
        )
        assert False, "Expected ValueError for ERROR without error_message"
    except ValueError as exc:
        assert "требуется error_message" in str(exc)
