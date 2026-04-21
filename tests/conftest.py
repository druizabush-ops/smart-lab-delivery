"""Глобальная test-изоляция окружения для deterministic backend-проверок."""

from __future__ import annotations

import os
from typing import Iterator

import pytest

_ISOLATED_SLD_ENV_KEYS = (
    "SLD_INTEGRATION_MODE",
    "SLD_REPOSITORY_MODE",
    "SLD_DATABASE_URL",
    "SLD_DB_HOST",
    "SLD_DB_PORT",
    "SLD_DB_NAME",
    "SLD_DB_USER",
    "SLD_DB_PASSWORD",
    "SLD_RENOVATIO_BASE_URL",
    "SLD_RENOVATIO_API_KEY",
    "SLD_RENOVATIO_API_VERSION",
)


@pytest.fixture(autouse=True)
def isolate_backend_test_env() -> Iterator[None]:
    """Очищает production-like SLD переменные до выполнения каждого теста.

    Важно: isolation применяется только в test bootstrap и не влияет на production runtime.
    """

    snapshot = {key: os.environ.get(key) for key in _ISOLATED_SLD_ENV_KEYS}
    for key in _ISOLATED_SLD_ENV_KEYS:
        os.environ.pop(key, None)

    yield

    for key, value in snapshot.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
