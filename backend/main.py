"""DisputeGuard — FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()  # Load .env before any other imports

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.services.case_loader import store


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Load synthetic fixture data once for each application startup."""
    store.load()
    yield

app = FastAPI(
    title="DisputeGuard API",
    description="Evidence-grounded AI for chargeback decisioning and representment.",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS origins supporting local development and Vercel production
default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
allowed_origins = list(default_origins)

frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    cleaned = frontend_url.strip().rstrip("/")
    if cleaned and cleaned not in allowed_origins:
        allowed_origins.append(cleaned)

allowed_origins_env = os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ORIGINS")
if allowed_origins_env:
    if allowed_origins_env.strip() == "*":
        allowed_origins = ["*"]
    else:
        for origin in allowed_origins_env.split(","):
            cleaned = origin.strip().rstrip("/")
            if cleaned and cleaned not in allowed_origins:
                allowed_origins.append(cleaned)

allow_origin_regex = os.getenv("ALLOWED_ORIGIN_REGEX", r"^https://.*\.vercel\.app$")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.get("/")
async def root():
    """Service status and discoverability root endpoint."""
    return {
        "status": "healthy",
        "service": "DisputeGuard API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8000")))
    uvicorn.run("backend.main:app", host=host, port=port, reload=(os.getenv("ENVIRONMENT") != "production"))

