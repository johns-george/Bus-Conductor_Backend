"""Request logging middleware with unique request IDs for tracing."""

import time
import logging
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("busconductor")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        # Attach request ID to scope so endpoints can read it
        scope = request.scope
        scope["request_id"] = request_id

        response = await call_next(request)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        client_ip = request.client.host if request.client else "-"

        logger.info(
            "%s %s %s %s %dms %s",
            request_id,
            request.method,
            request.url.path,
            client_ip,
            response.status_code,
            elapsed_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response
