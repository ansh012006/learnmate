"""LearnMate AI - FastAPI Application Entry Point"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database.config import engine, Base
from backend.database import models
from backend.api import router as api_router

# Ensure upload directory exists
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Frontend directory (sibling to backend/)
FRONTEND_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "frontend")
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="LearnMate AI",
    description="AI-Powered Study Assistant — Learn Smarter. Practice Better. Achieve More.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://localhost:3000")
origins = [o.strip() for o in CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes (must come before static mount so /api/v1/* takes priority)
app.include_router(api_router, prefix="/api/v1")

# Mount uploads directory
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Mount frontend static files (css, js, etc.)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"detail": "An internal error occurred. Please try again later."}
