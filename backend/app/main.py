from fastapi import FastAPI

from backend.app.api.repositories import router as repositories_router

app = FastAPI(
    title="IndraStra Harvester API",
    version="0.2.0",
    description="Scholarly metadata harvesting and discovery platform.",
)
app.include_router(repositories_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "indrastra-harvester"}


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {
        "name": "IndraStra Harvester",
        "version": "0.2.0",
        "status": "development",
    }
