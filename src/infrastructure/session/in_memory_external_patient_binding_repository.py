"""In-memory repository привязки внешнего user_id к patient session."""

from src.application.use_cases.patient_auth import ExternalPatientBinding


class InMemoryExternalPatientBindingRepository:
    def __init__(self) -> None:
        self._bindings: dict[str, ExternalPatientBinding] = {}

    def save(self, binding: ExternalPatientBinding) -> None:
        self._bindings[binding.external_platform_user_id] = binding

    def get(self, external_platform_user_id: str) -> ExternalPatientBinding | None:
        return self._bindings.get(external_platform_user_id)

    def delete(self, external_platform_user_id: str) -> None:
        self._bindings.pop(external_platform_user_id, None)
