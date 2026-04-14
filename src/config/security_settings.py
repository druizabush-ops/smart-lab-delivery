"""Security-конфигурация patient-facing и API hardening слоя."""

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class SecuritySettings:
    """Единая security-конфигурация минимального production hardening слоя."""

    patient_security_mode: str
    max_webapp_secret: str
    rate_limit_enabled: bool
    rate_limit_per_minute: int

    @classmethod
    def from_env(cls) -> "SecuritySettings":
        settings = cls(
            patient_security_mode=os.getenv("SLD_PATIENT_SECURITY_MODE", "relaxed"),
            max_webapp_secret=os.getenv("SLD_MAX_WEBAPP_SECRET", ""),
            rate_limit_enabled=os.getenv("SLD_RATE_LIMIT_ENABLED", "1") == "1",
            rate_limit_per_minute=int(os.getenv("SLD_RATE_LIMIT_PER_MINUTE", "120")),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        """Проверяет корректность security параметров."""

        if self.patient_security_mode not in {"relaxed", "strict"}:
            raise ValueError("SLD_PATIENT_SECURITY_MODE должен быть relaxed или strict")
        if self.rate_limit_per_minute <= 0:
            raise ValueError("SLD_RATE_LIMIT_PER_MINUTE должен быть > 0")
