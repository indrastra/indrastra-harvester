import logging
import os
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from opensearchpy.exceptions import OpenSearchException
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.app.api.analytics import router as analytics_router
from backend.app.api.auth import router as auth_router
from backend.app.api.exports import router as exports_router
from backend.app.api.harvests import router as harvests_router
from backend.app.api.indexing import router as indexing_router
from backend.app.api.records import router as records_router
from backend.app.api.repositories import router as repositories_router
from backend.app.api.schedules import router as schedules_router
from backend.app.api.search import router as search_router
from backend.app.db.session import SessionLocal
from backend.app.search.service import get_opensearch_client

logger = logging.getLogger("indrastra.api")

app = FastAPI(
    title="IndraStra Harvester API",
    version="0.11.0",
    description="Scholarly metadata harvesting and discovery platform.",
)
app.include_router(repositories_router, prefix="/api/v1")
app.include_router(exports_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(harvests_router, prefix="/api/v1")
app.include_router(schedules_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(records_router, prefix="/api/v1")
app.include_router(indexing_router, prefix="/api/v1")


@app.middleware("http")
async def add_security_headers_and_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    logger.info(
        "request_complete",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    )
    return response


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness probe: process is running."""
    return {"status": "ok", "service": "indrastra-harvester"}


@app.get("/ready", tags=["system"])
def readiness() -> dict[str, object]:
    """Readiness probe: database, Redis, and OpenSearch are reachable."""
    checks: dict[str, str] = {}

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except SQLAlchemyError:
        checks["database"] = "unavailable"

    redis_client = None
    try:
        redis_client = Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        redis_client.ping()
        checks["redis"] = "ok"
    except (RedisError, OSError, ValueError):
        checks["redis"] = "unavailable"
    finally:
        if redis_client is not None:
            redis_client.close()

    search_client = None
    try:
        search_client = get_opensearch_client()
        search_client.cluster.health(request_timeout=3)
        checks["opensearch"] = "ok"
    except (OpenSearchException, OSError, ValueError):
        checks["opensearch"] = "unavailable"
    finally:
        if search_client is not None:
            search_client.close()

    if any(value != "ok" for value in checks.values()):
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks}


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "name": "IndraStra Harvester",
        "version": "0.11.0",
        "status": "development",
    }
