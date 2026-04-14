"""Локальный запуск patient API через uvicorn."""

from pathlib import Path
import sys

import uvicorn

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.presentation.patient_api import create_patient_api_app

app = create_patient_api_app()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)
