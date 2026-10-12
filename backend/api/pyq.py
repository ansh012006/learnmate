import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from typing import List, Optional
from backend.pyq_analyzer.analyzer import analyze_pyq_document
from backend.database.config import get_db
from backend.database.models import PyqAnalysis
from sqlalchemy.orm import Session

router = APIRouter(prefix="/pyq", tags=["pyq"])


class PyqResponse(BaseModel):
    id: int
    filename: str
    question_count: int
    topics: List[dict]
    patterns: dict
    clusters: List[dict]
    difficulty_distribution: dict
    status: str
    analyzed_at: Optional[str] = None


class PyqListResponse(BaseModel):
    analyses: List[PyqResponse]
    total: int


@router.get("/", response_model=PyqListResponse)
async def list_pyq_analyses(db: Session = Depends(get_db)):
    analyses = db.query(PyqAnalysis).order_by(PyqAnalysis.analyzed_at.desc()).all()
    return {
        "analyses": [_format_pyq(a) for a in analyses],
        "total": len(analyses),
    }


@router.post("/upload", response_model=PyqResponse)
async def upload_pyq(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        os.makedirs(upload_dir, exist_ok=True)
        temp_path = os.path.join(upload_dir, f"pyq_temp_{file.filename}")

        with open(temp_path, "wb") as f:
            f.write(content)

        analysis = PyqAnalysis(
            filename=file.filename,
            question_count=0,
            status="processing",
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        result = analyze_pyq_document(temp_path, file.filename)
        os.remove(temp_path)

        analysis.question_count = result.get("question_count", 0)
        analysis.topics = result.get("topics", [])
        analysis.patterns = result.get("patterns", {})
        analysis.clusters = result.get("clusters", [])
        analysis.difficulty_distribution = result.get("difficulty_distribution", {})
        analysis.status = result.get("status", "completed")
        if result.get("error"):
            analysis.status = "error"

        db.commit()
        return _format_pyq(analysis)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


def _format_pyq(a: PyqAnalysis) -> dict:
    return {
        "id": a.id,
        "filename": a.filename,
        "question_count": a.question_count,
        "topics": a.topics or [],
        "patterns": a.patterns or {},
        "clusters": a.clusters or [],
        "difficulty_distribution": a.difficulty_distribution or {},
        "status": a.status,
        "analyzed_at": a.analyzed_at.isoformat() if a.analyzed_at else None,
    }
