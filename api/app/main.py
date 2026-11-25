"""FastAPI Main Application Entrypoint for AskLens."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import chat, schema

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("asklens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    logger.info("Initializing AskLens AI Data Analyst Platform...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Primary LLM: {settings.LLM_PROVIDER}")
    yield
    logger.info("Shutting down AskLens API.")


app = FastAPI(
    title="AskLens API",
    description="Autonomous Senior AI Data Analyst & Scientist Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js web application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(chat.router)
app.include_router(schema.router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AskLens API",
        "llm_provider": settings.LLM_PROVIDER,
        "database": settings.POSTGRES_DB
    }
