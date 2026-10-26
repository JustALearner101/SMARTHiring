import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exception.CustomException import AppException

logger = logging.getLogger("heketon.api")


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform global exception handlers for the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "data": exc.data,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail_msg = exc.detail if isinstance(exc.detail, str) else "Terjadi kesalahan pada request"
        data_payload: Any = None
        if isinstance(exc.detail, dict):
            detail_msg = exc.detail.get("message", "Terjadi kesalahan pada request")
            data_payload = exc.detail.get("data")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": detail_msg,
                "data": data_payload,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        formatted_errors = []
        for error in exc.errors():
            loc = " -> ".join([str(part) for part in error.get("loc", []) if part != "body"])
            formatted_errors.append(
                {
                    "field": loc or "payload",
                    "message": error.get("msg", "Format input tidak valid"),
                }
            )

        summary_msg = (
            f"Validasi input gagal: field '{formatted_errors[0]['field']}' ({formatted_errors[0]['message']})"
            if formatted_errors
            else "Validasi input gagal"
        )

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": summary_msg,
                "data": {"errors": formatted_errors},
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server exception at %s %s: %s", request.method, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Terjadi kesalahan internal pada server. Silakan hubungi admin.",
                "data": None,
            },
        )
