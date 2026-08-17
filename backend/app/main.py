from fastapi import FastAPI

from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Control plane for securely managing business AI agents.",
    version=settings.app_version,
    debug=settings.debug,
)


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {
        "message": f"{settings.app_name} is running"
    }


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "deployguard-api",
        "version": settings.app_version,
        "environment": settings.environment,
    }