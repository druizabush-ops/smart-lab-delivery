"""Runtime-конфигурация режимов репозитория и интеграций."""

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Единая runtime-конфигурация верхнего уровня приложения."""

    repository_mode: str
    integration_mode: str

    @classmethod
    def from_env(cls) -> "RuntimeSettings":
        """Считывает режимы запуска из переменных окружения."""

        return cls(
            repository_mode=os.getenv("SLD_REPOSITORY_MODE", "in_memory"),
            integration_mode=os.getenv("SLD_INTEGRATION_MODE", "stub"),
        )
