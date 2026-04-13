"""Сервис orchestration потока доставки в application-слое."""

from src.application.interfaces import LabResultProvider
from src.application.use_cases import CreateDeliveryCardUseCase, ProcessDeliveryUseCase
from src.domain.entities import DeliveryCard, LabResult, Patient


class DeliveryOrchestrator:
    """Оркеструет поток LabResult -> DeliveryCard -> DeliveryAttempt -> Status update."""

    def __init__(
        self,
        lab_result_provider: LabResultProvider,
        create_delivery_card_use_case: CreateDeliveryCardUseCase,
        process_delivery_use_case: ProcessDeliveryUseCase,
    ) -> None:
        self._lab_result_provider = lab_result_provider
        self._create_delivery_card_use_case = create_delivery_card_use_case
        self._process_delivery_use_case = process_delivery_use_case

    def orchestrate(self, patient: Patient, lab_result: LabResult) -> DeliveryCard:
        """Оркестрирует полный жизненный цикл карточки для одной пары patient/result."""

        card = self._create_delivery_card_use_case.execute(patient, lab_result)
        return self._process_delivery_use_case.execute(card)

    def orchestrate_ready_results(self, patients: dict[str, Patient]) -> list[DeliveryCard]:
        """Обрабатывает все готовые результаты через переданную карту пациентов."""

        cards: list[DeliveryCard] = []
        for result in self._lab_result_provider.get_ready_results():
            patient = patients.get(result.patient_id)
            if patient is None:
                continue

            cards.append(self.orchestrate(patient, result))

        return cards
