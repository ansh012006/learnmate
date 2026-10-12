from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from backend.api.health import router as health_router
from backend.api.chat import router as chat_router
from backend.api.documents import router as documents_router
from backend.api.pyq import router as pyq_router
from backend.api.quiz import router as quiz_router
from backend.api.planner import router as planner_router
from backend.api.analytics import router as analytics_router

from backend.database.config import engine, Base
from backend.database import models

Base.metadata.create_all(bind=engine)

router = APIRouter()

router.include_router(health_router, tags=["health"])
router.include_router(chat_router, tags=["chat"])
router.include_router(documents_router, tags=["documents"])
router.include_router(pyq_router, tags=["pyq"])
router.include_router(quiz_router, tags=["quiz"])
router.include_router(planner_router, tags=["planner"])
router.include_router(analytics_router, tags=["analytics"])


@router.get("/")
async def root():
    return {
        "app": "LearnMate AI",
        "version": "1.0.0",
        "tagline": "Learn Smarter. Practice Better. Achieve More.",
        "docs": "/docs",
    }
