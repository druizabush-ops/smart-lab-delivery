"""Локальный запуск operator API (read-only) через uvicorn."""

import uvicorn

from src.presentation.operator_api import create_operator_api_app

app = create_operator_api_app()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
