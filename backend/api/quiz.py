from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

from backend.services.llm_service import llm_service
from backend.rag.pipeline import document_store
from backend.database.config import get_db
from backend.database.models import Quiz, QuizAttempt
from sqlalchemy.orm import Session

router = APIRouter(prefix="/quiz", tags=["quiz"])


class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=255)
    num_questions: int = Field(5, ge=3, le=20)
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    source_document_ids: Optional[List[int]] = None


class QuizSubmitRequest(BaseModel):
    quiz_id: int
    answers: List[int]


class QuizResponse(BaseModel):
    id: int
    title: str
    topic: str
    questions: List[dict]
    difficulty: str
    created_at: Optional[str] = None


class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    score: float
    total_questions: int
    correct_answers: int
    completed_at: Optional[str] = None


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest, db: Session = Depends(get_db)):
    try:
        context = ""
        if request.source_document_ids:
            all_chunks = []
            for doc_id in request.source_document_ids:
                docs = document_store.retrieve(request.topic, top_k=10)
                all_chunks.extend([d["text"] for d in docs])
            context = "\n\n".join(all_chunks[:3000])

        questions = llm_service.generate_quiz_questions(
            context=context or f"Topic: {request.topic}",
            num_questions=request.num_questions,
            topic=request.topic,
        )

        if not questions:
            raise HTTPException(
                status_code=500,
                detail="Could not generate quiz questions. Please try again."
            )

        quiz = Quiz(
            title=f"{request.topic} - Quiz",
            topic=request.topic,
            source_document_ids=request.source_document_ids or [],
            questions=questions,
            difficulty=request.difficulty,
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        return QuizResponse(
            id=quiz.id,
            title=quiz.title,
            topic=quiz.topic,
            questions=quiz.questions,
            difficulty=quiz.difficulty,
            created_at=quiz.created_at.isoformat() if quiz.created_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit", response_model=QuizAttemptResponse)
async def submit_quiz(request: QuizSubmitRequest, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == request.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = quiz.questions or []
    if len(request.answers) != len(questions):
        raise HTTPException(
            status_code=400,
            detail=f"Expected {len(questions)} answers, got {len(request.answers)}"
        )

    correct = 0
    for i, q in enumerate(questions):
        if i < len(request.answers) and request.answers[i] == q.get("correct_answer"):
            correct += 1

    score = (correct / len(questions)) * 100

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        score=score,
        total_questions=len(questions),
        correct_answers=correct,
        answers=request.answers,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return QuizAttemptResponse(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        score=attempt.score,
        total_questions=attempt.total_questions,
        correct_answers=attempt.correct_answers,
        completed_at=attempt.completed_at.isoformat() if attempt.completed_at else None,
    )


@router.get("/history")
async def quiz_history(db: Session = Depends(get_db)):
    attempts = db.query(QuizAttempt).order_by(QuizAttempt.completed_at.desc()).limit(20).all()
    return {
        "attempts": [
            {
                "id": a.id,
                "quiz_id": a.quiz_id,
                "score": a.score,
                "total_questions": a.total_questions,
                "correct_answers": a.correct_answers,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            }
            for a in attempts
        ]
    }
