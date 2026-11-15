from fastapi import FastAPI

app = FastAPI(
    title="IndraStra Harvester API",
    version="0.1.0",
    description="Scholarly metadata harvesting and discovery platform.",
)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "indrastra-harvester"}


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {
        "name": "IndraStra Harvester",
        "version": "0.1.0",
        "status": "scaffold",
    }
