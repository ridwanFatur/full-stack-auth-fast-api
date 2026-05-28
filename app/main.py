from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import app.models  # noqa: F401 — registers all ORM models in SQLAlchemy's mapper registry
from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.agents.agent import Agent

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FastAPI monolith backend with Google OAuth and JWT authentication.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app.state.agent = Agent()
    
    yield
    
# CORS — allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include versioned API router
app.include_router(api_v1_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "service": settings.PROJECT_NAME}
