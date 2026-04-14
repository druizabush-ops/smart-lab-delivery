"""Валидация launch/release режимов и обязательных env-контрактов."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class LaunchValidationResult:
    """Результат проверки launch-конфигурации."""

    profile: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """Показывает, можно ли запускать систему в выбранном профиле."""

        return not self.errors


class LaunchModeValidator:
    """Проверяет обязательные env и unsafe-default значения перед go-live."""

    _ALLOWED_PROFILES = frozenset({"dev", "test", "staging", "prod"})

    def validate(self, profile: str) -> LaunchValidationResult:
        """Выполняет проверку env-контракта для указанного профиля."""

        if profile not in self._ALLOWED_PROFILES:
            raise ValueError("profile должен быть dev, test, staging или prod")

        errors: list[str] = []
        warnings: list[str] = []

        repository_mode = os.getenv("SLD_REPOSITORY_MODE", "in_memory")
        integration_mode = os.getenv("SLD_INTEGRATION_MODE", "stub")

        if profile in {"staging", "prod"}:
            self._validate_release_like(errors, warnings, profile=profile, repository_mode=repository_mode, integration_mode=integration_mode)
        else:
            self._validate_non_release_like(warnings, profile=profile, repository_mode=repository_mode)

        return LaunchValidationResult(profile=profile, errors=tuple(errors), warnings=tuple(warnings))

    def _validate_non_release_like(self, warnings: list[str], *, profile: str, repository_mode: str) -> None:
        if repository_mode == "in_memory":
            warnings.append(f"{profile}: используется in_memory repository — данные не сохраняются между перезапусками")

    def _validate_release_like(
        self,
        errors: list[str],
        warnings: list[str],
        *,
        profile: str,
        repository_mode: str,
        integration_mode: str,
    ) -> None:
        if repository_mode != "postgres":
            errors.append(f"{profile}: SLD_REPOSITORY_MODE должен быть postgres")

        if integration_mode != "real":
            errors.append(f"{profile}: SLD_INTEGRATION_MODE должен быть real")

        required_non_empty = (
            "SLD_DATABASE_URL",
            "SLD_RENOVATIO_API_KEY",
            "SLD_MAX_BOT_TOKEN",
            "SLD_MAX_BOT_NAME",
            "SLD_EMAIL_SMTP_HOST",
            "SLD_EMAIL_FROM",
            "SLD_MAX_WEBAPP_SECRET",
        )
        for key in required_non_empty:
            if not os.getenv(key, "").strip():
                errors.append(f"{profile}: обязательная переменная {key} не задана")

        if os.getenv("SLD_PATIENT_SECURITY_MODE", "relaxed") != "strict":
            errors.append(f"{profile}: SLD_PATIENT_SECURITY_MODE должен быть strict")

        db_url = os.getenv("SLD_DATABASE_URL", "")
        if "postgres:postgres" in db_url:
            errors.append(f"{profile}: SLD_DATABASE_URL использует небезопасный default postgres:postgres")

        if os.getenv("SLD_EMAIL_SMTP_HOST", "").strip().lower() == "localhost":
            errors.append(f"{profile}: SLD_EMAIL_SMTP_HOST=localhost недопустим для release-like режима")

        max_base_url = os.getenv("SLD_MAX_BASE_URL", "https://platform-api.max.ru")
        if "example" in max_base_url:
            errors.append(f"{profile}: SLD_MAX_BASE_URL содержит example-заглушку")

        mapping_value = os.getenv("SLD_MAX_PATIENT_RECIPIENT_MAP", "").strip()
        if not mapping_value:
            warnings.append(f"{profile}: SLD_MAX_PATIENT_RECIPIENT_MAP не задан, часть MAX-отправок может перейти в ошибки")
