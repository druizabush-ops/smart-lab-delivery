"""Stub-адаптер отправки через канал EMAIL."""

from datetime import datetime

from src.application.interfaces import DeliveryProvider
from src.domain.entities import DeliveryAttempt, DeliveryCard, DeliveryChannel
from src.domain.statuses import AttemptStatus


class EmailDeliveryProvider(DeliveryProvider):
    """Эмулирует отправку email на основе простых правил валидации."""

    def send(self, card: DeliveryCard) -> DeliveryAttempt:
        if card.channel is not DeliveryChannel.EMAIL:
            return DeliveryAttempt(
                timestamp=datetime.utcnow(),
                channel=DeliveryChannel.EMAIL,
                result=AttemptStatus.ERROR,
                error_message="Email provider получил карточку с неподдерживаемым каналом.",
            )

        if card.patient_id.endswith("3"):
            return DeliveryAttempt(
                timestamp=datetime.utcnow(),
                channel=DeliveryChannel.EMAIL,
                result=AttemptStatus.ERROR,
                error_message="EMAIL stub: имитация недоступности SMTP-провайдера.",
            )

        return DeliveryAttempt(
            timestamp=datetime.utcnow(),
            channel=DeliveryChannel.EMAIL,
            result=AttemptStatus.SUCCESS,
        )
