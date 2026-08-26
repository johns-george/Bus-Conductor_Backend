"""Global exception handler — catches unhandled errors and returns
consistent JSON responses instead of raw 500s."""

import logging
import traceback
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("busconductor")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException:
            raise  # Let FastAPI handle its own HTTPExceptions
        except Exception as exc:
            request_id = request.scope.get("request_id", "?")
            logger.error(
                "[%s] Unhandled exception on %s %s: %s\n%s",
                request_id,
                request.method,
                request.url.path,
                exc,
                traceback.format_exc(),
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id,
                },
            )
