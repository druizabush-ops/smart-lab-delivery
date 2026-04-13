"""Stub-адаптер отправки через канал MAX."""

from datetime import datetime

from src.application.interfaces import DeliveryProvider
from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel
from src.domain.statuses import AttemptStatus


class MaxDeliveryProvider(DeliveryProvider):
    """Эмулирует отправку в MAX по простой deterministic-логике."""

    def send(self, card: DeliveryCard) -> DeliveryAttempt:
        if card.channel is not DeliveryChannel.MAX:
            return DeliveryAttempt(
                timestamp=datetime.utcnow(),
                channel=DeliveryChannel.MAX,
                result=AttemptStatus.ERROR,
                error_message="MAX provider получил карточку с неподдерживаемым каналом.",
            )

        is_error = card.lab_result_id.endswith("2")
        if is_error:
            return DeliveryAttempt(
                timestamp=datetime.utcnow(),
                channel=DeliveryChannel.MAX,
                result=AttemptStatus.ERROR,
                error_message="MAX stub: имитация временной ошибки отправки.",
            )

        return DeliveryAttempt(
            timestamp=datetime.utcnow(),
            channel=DeliveryChannel.MAX,
            result=AttemptStatus.SUCCESS,
        )
