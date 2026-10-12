from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

from backend.database.config import get_db
from backend.database.models import Document, ChatMessage, PyqAnalysis, Quiz, QuizAttempt, StudyTask
from sqlalchemy.orm import Session
from sqlalchemy import func

router = APIRouter(prefix="/analytics", tags=["analytics"])


class AnalyticsResponse(BaseModel):
    documents: Dict
    pyq: Dict
    quizzes: Dict
    tasks: Dict
    learning: Dict
    recent_activity: List[Dict]


@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_analytics(db: Session = Depends(get_db)):
    total_docs = db.query(func.count(Document.id)).scalar() or 0
    ready_docs = db.query(func.count(Document.id)).filter(Document.status == "ready").scalar() or 0
    total_chunks = db.query(func.sum(Document.chunk_count)).scalar() or 0

    total_pyq = db.query(func.count(PyqAnalysis.id)).scalar() or 0
    total_questions = db.query(func.sum(PyqAnalysis.question_count)).scalar() or 0

    total_quizzes = db.query(func.count(Quiz.id)).scalar() or 0
    total_attempts = db.query(func.count(QuizAttempt.id)).scalar() or 0
    avg_score = db.query(func.avg(QuizAttempt.score)).scalar() or 0.0

    total_tasks = db.query(func.count(StudyTask.id)).scalar() or 0
    completed_tasks = db.query(func.count(StudyTask.id)).filter(StudyTask.status == "completed").scalar() or 0

    week_ago = datetime.now() - __import__('datetime').timedelta(days=7)
    weekly_chats = db.query(func.count(ChatMessage.id)).filter(
        ChatMessage.created_at >= week_ago,
        ChatMessage.role == "user"
    ).scalar() or 0

    recent_messages = db.query(ChatMessage).filter(
        ChatMessage.role == "user"
    ).order_by(ChatMessage.created_at.desc()).limit(5).all()

    recent_activity = [
        {
            "type": "chat",
            "content": m.content[:100],
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in recent_messages
    ]

    recent_attempts = db.query(QuizAttempt).order_by(
        QuizAttempt.completed_at.desc()
    ).limit(10).all()

    score_history = [
        {
            "quiz_id": a.quiz_id,
            "score": a.score,
            "completed_at": a.completed_at.isoformat() if a.completed_at else None,
        }
        for a in recent_attempts
    ]

    return {
        "documents": {
            "total": total_docs,
            "ready": ready_docs,
            "total_chunks": total_chunks,
        },
        "pyq": {
            "total_analyses": total_pyq,
            "total_questions": total_questions or 0,
        },
        "quizzes": {
            "total": total_quizzes,
            "attempts": total_attempts,
            "avg_score": round(float(avg_score), 1),
            "score_history": score_history,
        },
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
            "completion_rate": round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0,
        },
        "learning": {
            "weekly_chats": weekly_chats,
            "total_chat_sessions": db.query(func.count(func.distinct(ChatMessage.session_id))).scalar() or 0,
        },
        "recent_activity": recent_activity,
    }
