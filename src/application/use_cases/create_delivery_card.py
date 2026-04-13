"""Use case создания карточки доставки из доменных данных."""

from src.domain.entities import DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import LabResultStatus


class CreateDeliveryCardUseCase:
    """Создает DeliveryCard для готового результата пациента."""

    def __init__(self, default_channel: DeliveryChannel = DeliveryChannel.MAX) -> None:
        self._default_channel = default_channel

    def execute(self, patient: Patient, lab_result: LabResult) -> DeliveryCard:
        """Создает карточку с начальным статусом, определенным доменной фабрикой."""

        if lab_result.status is not LabResultStatus.READY:
            raise ValueError("DeliveryCard можно создавать только для LabResult в статусе READY.")

        if lab_result.patient_id != patient.id:
            raise ValueError("patient.id должен совпадать с lab_result.patient_id.")

        return DeliveryCard.create(
            patient_id=patient.id,
            lab_result_id=lab_result.id,
            channel=self._default_channel,
        )
