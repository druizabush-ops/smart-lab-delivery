"""Structured logging bootstrap для runtime/API контуров."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging


class JsonLogFormatter(logging.Formatter):
    """Форматтер JSON-подобного structured лога."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra_fields = [
            "command",
            "card_id",
            "success",
            "reason",
            "actor",
            "source",
            "error",
            "correlation_id",
            "path",
            "method",
            "status_code",
            "queue_status",
            "processed_count",
        ]
        for field in extra_fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    """Настраивает единый логер приложения."""

    root = logging.getLogger()
    if getattr(root, "_sld_configured", False):
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())

    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    setattr(root, "_sld_configured", True)
