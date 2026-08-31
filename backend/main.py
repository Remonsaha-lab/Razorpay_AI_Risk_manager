"""DisputeGuard — FastAPI application entry point."""

from dotenv import load_dotenv
load_dotenv()  # Load .env before any other imports

from contextlib import asynccontextmanager

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

# Allow the Next.js frontend (port 3000) to call this API (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
