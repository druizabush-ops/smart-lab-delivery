"""Runtime-конфигурация режимов репозитория и интеграций."""

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Единая runtime-конфигурация верхнего уровня приложения."""

    repository_mode: str
    integration_mode: str
    environment: str

    @classmethod
    def from_env(cls) -> "RuntimeSettings":
        """Считывает режимы запуска из переменных окружения и валидирует их."""

        settings = cls(
            repository_mode=os.getenv("SLD_REPOSITORY_MODE", "in_memory"),
            integration_mode=os.getenv("SLD_INTEGRATION_MODE", "stub"),
            environment=os.getenv("SLD_ENV", "dev"),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        """Проверяет корректность runtime-режимов."""

        if self.repository_mode not in {"in_memory", "postgres"}:
            raise ValueError("SLD_REPOSITORY_MODE должен быть in_memory или postgres")
        if self.integration_mode not in {"stub", "real"}:
            raise ValueError("SLD_INTEGRATION_MODE должен быть stub или real")
        if self.environment not in {"dev", "test", "prod"}:
            raise ValueError("SLD_ENV должен быть dev, test или prod")
