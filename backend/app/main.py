from fastapi import FastAPI

from backend.app.api.analytics import router as analytics_router
from backend.app.api.auth import router as auth_router
from backend.app.api.exports import router as exports_router
from backend.app.api.harvests import router as harvests_router
from backend.app.api.indexing import router as indexing_router
from backend.app.api.records import router as records_router
from backend.app.api.repositories import router as repositories_router
from backend.app.api.schedules import router as schedules_router
from backend.app.api.search import router as search_router

app = FastAPI(
    title="IndraStra Harvester API",
    version="0.10.0",
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


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "indrastra-harvester"}


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {
        "name": "IndraStra Harvester",
        "version": "0.10.0",
        "status": "development",
    }
