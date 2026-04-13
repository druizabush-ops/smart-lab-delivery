"""Явный mapping между domain DeliveryCard и ORM persistence моделями."""

from src.domain.entities import DeliveryAttempt, DeliveryCard
from src.domain.entities.channels import DeliveryChannel
from src.domain.statuses import AttemptStatus, DeliveryStatus, QueueStatus
from src.infrastructure.persistence.models import DeliveryAttemptModel, DeliveryCardModel


class DeliveryCardMapper:
    """Конвертеры domain <-> persistence без утечки ORM в domain."""

    @staticmethod
    def to_model(card_id: str, card: DeliveryCard) -> DeliveryCardModel:
        model = DeliveryCardModel(
            card_id=card_id,
            patient_id=card.patient_id,
            lab_result_id=card.lab_result_id,
            status=card.status.value,
            queue_status=card.queue_status.value,
            channel=card.channel.value,
            created_at=card.created_at,
            updated_at=card.updated_at,
        )
        model.attempts = [
            DeliveryAttemptModel(
                sequence_no=index,
                timestamp=attempt.timestamp,
                channel=attempt.channel.value,
                result=attempt.result.value,
                error_message=attempt.error_message,
            )
            for index, attempt in enumerate(card.attempts)
        ]
        return model

    @staticmethod
    def update_model(model: DeliveryCardModel, card: DeliveryCard) -> None:
        model.patient_id = card.patient_id
        model.lab_result_id = card.lab_result_id
        model.status = card.status.value
        model.queue_status = card.queue_status.value
        model.channel = card.channel.value
        model.created_at = card.created_at
        model.updated_at = card.updated_at
        model.attempts = [
            DeliveryAttemptModel(
                sequence_no=index,
                timestamp=attempt.timestamp,
                channel=attempt.channel.value,
                result=attempt.result.value,
                error_message=attempt.error_message,
            )
            for index, attempt in enumerate(card.attempts)
        ]

    @staticmethod
    def to_domain(model: DeliveryCardModel) -> DeliveryCard:
        attempts = [
            DeliveryAttempt(
                timestamp=attempt.timestamp,
                channel=DeliveryChannel(attempt.channel),
                result=AttemptStatus(attempt.result),
                error_message=attempt.error_message,
            )
            for attempt in sorted(model.attempts, key=lambda item: item.sequence_no)
        ]
        return DeliveryCard(
            patient_id=model.patient_id,
            lab_result_id=model.lab_result_id,
            status=DeliveryStatus(model.status),
            queue_status=QueueStatus(model.queue_status),
            channel=DeliveryChannel(model.channel),
            attempts=attempts,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
