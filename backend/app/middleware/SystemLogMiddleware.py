import asyncio
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.repository.SystemLogRepository import SystemLogRepository

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
EXCLUDED_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class SystemLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        method = request.method

        # Skip docs and health check endpoints
        if any(path.startswith(excluded) for excluded in EXCLUDED_PATHS):
            return await call_next(request)

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Log mutating actions (Add/Update/Delete) or client errors (4xx)
        status_code = response.status_code
        should_log = method in MUTATING_METHODS or status_code >= 400

        if should_log:
            level = "WARN" if status_code >= 400 else "INFO"
            message = f"Transaction {method} {path} completed with status {status_code} in {duration_ms}ms"

            # Execute log insertion in background task to avoid response delay
            asyncio.create_task(
                SystemLogRepository.log_direct(
                    vlog_level=level,
                    vlog_message=message,
                    vlog_source="HTTP_GATEWAY",
                    vlog_path=path,
                    vlog_method=method,
                    vlog_status_code=str(status_code),
                )
            )

        return response