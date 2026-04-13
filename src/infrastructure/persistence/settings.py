"""Конфигурация persistence слоя из переменных окружения."""

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    """Параметры подключения к PostgreSQL."""

    host: str
    port: int
    name: str
    user: str
    password: str
    url: str

    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        host = os.getenv("SLD_DB_HOST", "localhost")
        port = int(os.getenv("SLD_DB_PORT", "5432"))
        name = os.getenv("SLD_DB_NAME", "smart_lab_delivery")
        user = os.getenv("SLD_DB_USER", "postgres")
        password = os.getenv("SLD_DB_PASSWORD", "postgres")
        url = os.getenv(
            "SLD_DATABASE_URL",
            f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}",
        )
        return cls(host=host, port=port, name=name, user=user, password=password, url=url)
