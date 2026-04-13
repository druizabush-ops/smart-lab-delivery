"""Runtime-конфигурация выбора режима хранения."""

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    repository_mode: str

    @classmethod
    def from_env(cls) -> "RuntimeSettings":
        return cls(repository_mode=os.getenv("SLD_REPOSITORY_MODE", "in_memory"))
