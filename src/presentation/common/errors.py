"""Унифицированные error contracts для API."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("sld.api.errors")


def _error_payload(code: str, message: str, correlation_id: str) -> dict[str, str]:
    return {
        "code": code,
        "message": message,
        "correlation_id": correlation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def register_error_handlers(app: FastAPI) -> None:
    """Регистрирует единый набор обработчиков ошибок."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", str(uuid4()))
        logger.warning(
            "api_http_error",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
                "correlation_id": correlation_id,
            },
        )
        message = exc.detail if isinstance(exc.detail, str) else "Ошибка запроса"
        return JSONResponse(status_code=exc.status_code, content=_error_payload("http_error", message, correlation_id))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", str(uuid4()))
        logger.warning(
            "api_validation_error",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": 422,
                "correlation_id": correlation_id,
            },
        )
        return JSONResponse(
            status_code=422,
            content=_error_payload("validation_error", "Некорректные параметры запроса", correlation_id),
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", str(uuid4()))
        logger.exception(
            "api_unhandled_error",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": 500,
                "correlation_id": correlation_id,
            },
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content=_error_payload("internal_error", "Внутренняя ошибка сервера", correlation_id),
        )
