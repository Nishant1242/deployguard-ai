from fastapi import FastAPI


app = FastAPI(
    title="DeployGuard AI API",
    description="Control plane for securely managing business AI agents.",
    version="0.1.0",
)


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {
        "message": "DeployGuard AI API is running"
    }


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "deployguard-api",
        "version": "0.1.0",
    }