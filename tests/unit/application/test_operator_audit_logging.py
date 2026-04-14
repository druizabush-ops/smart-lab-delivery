from src.application.services.policies import OperatorActionPolicy
from src.application.use_cases.operator_commands import (
    MoveToManualReviewCommandUseCase,
    OperatorCommandAuditContext,
)
from src.domain.entities import DeliveryCard, DeliveryChannel, LabResult, Patient
from src.domain.statuses import LabResultStatus
from src.infrastructure.identity import build_operational_card_id
from src.infrastructure.repositories import InMemoryDeliveryCardRepository


class SpyLogger:
    def __init__(self) -> None:
        self.events = []

    def log_action(self, **kwargs) -> None:
        self.events.append(kwargs)


def test_operator_command_writes_extended_audit_fields() -> None:
    repository = InMemoryDeliveryCardRepository()
    patient = Patient(id="p-1", full_name="Test", email="test@example.org")
    result = LabResult(id="lr-1", patient_id="p-1", status=LabResultStatus.READY)
    card = DeliveryCard.create(patient=patient, lab_result=result, channel=DeliveryChannel.MAX)
    card_id = build_operational_card_id(card)
    repository.save(card)

    logger = SpyLogger()
    use_case = MoveToManualReviewCommandUseCase(repository, OperatorActionPolicy(), action_logger=logger)

    use_case.execute(
        card_id,
        reason="проверка",
        context=OperatorCommandAuditContext(reason="проверка", actor="op-1", source="ui"),
    )

    assert len(logger.events) == 1
    event = logger.events[0]
    assert event["actor"] == "op-1"
    assert event["source"] == "ui"
    assert event["reason"] == "проверка"
