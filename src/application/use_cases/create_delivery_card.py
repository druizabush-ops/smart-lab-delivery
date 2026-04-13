"""Use case создания карточки доставки из доменных данных."""

from src.domain.entities import DeliveryCard, DeliveryChannel, LabResult, Patient


class CreateDeliveryCardUseCase:
    """Создает DeliveryCard для готового результата пациента."""

    def __init__(self, default_channel: DeliveryChannel = DeliveryChannel.MAX) -> None:
        self._default_channel = default_channel

    def execute(self, patient: Patient, lab_result: LabResult) -> DeliveryCard:
        """Создает карточку с начальным статусом, определенным доменной фабрикой."""

        return DeliveryCard.create(
            patient=patient,
            lab_result=lab_result,
            channel=self._default_channel,
        )
