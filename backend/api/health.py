from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "app": "LearnMate AI",
        "version": "1.0.0"
    }
