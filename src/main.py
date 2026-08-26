import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text

from src.core.config import settings
from src.core.database import Base, engine
from src.middleware.rate_limit import RateLimitMiddleware
from src.middleware.logging import RequestLoggingMiddleware
from src.middleware.error_handler import ErrorHandlerMiddleware

# ── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("busconductor")


# ── Lifespan (replaces deprecated on_event) ────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — creating tables if needed")
    Base.metadata.create_all(bind=engine)
    logger.info("Startup complete")
    yield
    logger.info("Shutting down")
    engine.dispose()


# ── App ────────────────────────────────────────────────────
app = FastAPI(
    title="Bus Conductor API",
    version="1.0.0",
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
    lifespan=lifespan,
)

# ── Middleware (order matters: last added = first executed) ─
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)


# ── CORS ───────────────────────────────────────────────────
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    allowed = settings.ALLOWED_ORIGINS

    # Check if origin is allowed
    origin_allowed = (
        "*" in allowed
        or (origin and origin in allowed)
        or (origin and any(o.rstrip("/") == origin.rstrip("/") for o in allowed))
    )

    # Preflight
    if request.method == "OPTIONS":
        resp = Response(status_code=204)
        if origin_allowed and origin:
            resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        resp.headers["Access-Control-Max-Age"] = "600"
        return resp

    resp = await call_next(request)
    if origin_allowed and origin:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Credentials"] = "true"
    return resp


# ── Health Check ───────────────────────────────────────────
@app.get("/health")
def health():
    """Health check endpoint for load balancers and orchestrators."""
    return {"status": "healthy", "service": "bus-conductor-api"}


@app.get("/")
def root():
    return {"message": "API running 🚀", "version": "1.0.0"}


@app.get("/test-db")
def test_db():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return {"status": "connected", "result": [row[0] for row in result]}
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        return JSONResponse(
            status_code=503,
            content={"status": "disconnected", "error": str(e)},
        )


# ── Routes ─────────────────────────────────────────────────
from src.api.routes import (
    auth,
    booking,
    bus,
    routes_catalog,
    conductor,
    admin,
    payment,
    payment_method,
    qr,
    search,
    stop,
    ticket,
    transaction,
    user,
    wallet,
)

app.include_router(auth.router)
app.include_router(booking.router)
app.include_router(bus.router)
app.include_router(conductor.router)
app.include_router(admin.router)
app.include_router(payment.router)
app.include_router(payment_method.router)
app.include_router(qr.router)
app.include_router(routes_catalog.router)
app.include_router(search.router)
app.include_router(stop.router)
app.include_router(ticket.router)
app.include_router(transaction.router)
app.include_router(user.router)
app.include_router(wallet.router)
