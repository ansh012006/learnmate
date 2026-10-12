from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from backend.database.config import get_db
from backend.database.models import StudyTask
from sqlalchemy.orm import Session
from sqlalchemy import func

router = APIRouter(prefix="/planner", tags=["planner"])


class StudyTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    subject: str = Field(..., min_length=1, max_length=255)
    topic: str = Field("", max_length=255)
    priority: str = Field("medium", pattern="^(low|medium|high)$")
    deadline: Optional[str] = None
    estimated_hours: float = Field(1.0, ge=0.5, le=24)


class StudyTaskUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed)$")
    deadline: Optional[str] = None
    estimated_hours: Optional[float] = Field(None, ge=0.5, le=24)


class StudyTaskResponse(BaseModel):
    id: int
    title: str
    subject: str
    topic: str
    priority: str
    status: str
    deadline: Optional[str] = None
    estimated_hours: float
    completed_at: Optional[str] = None
    created_at: Optional[str] = None


@router.get("/tasks", response_model=List[StudyTaskResponse])
async def list_tasks(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(StudyTask)
    if status:
        query = query.filter(StudyTask.status == status)
    tasks = query.order_by(StudyTask.priority.desc(), StudyTask.deadline).all()
    return [_format_task(t) for t in tasks]


@router.post("/tasks", response_model=StudyTaskResponse)
async def create_task(task: StudyTaskCreate, db: Session = Depends(get_db)):
    try:
        deadline_dt = None
        if task.deadline:
            deadline_dt = datetime.fromisoformat(task.deadline)

        db_task = StudyTask(
            title=task.title,
            subject=task.subject,
            topic=task.topic,
            priority=task.priority,
            deadline=deadline_dt,
            estimated_hours=task.estimated_hours,
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return _format_task(db_task)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tasks/{task_id}", response_model=StudyTaskResponse)
async def update_task(task_id: int, task: StudyTaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(StudyTask).filter(StudyTask.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.title is not None:
        db_task.title = task.title
    if task.subject is not None:
        db_task.subject = task.subject
    if task.topic is not None:
        db_task.topic = task.topic
    if task.priority is not None:
        db_task.priority = task.priority
    if task.status is not None:
        db_task.status = task.status
        if task.status == "completed":
            db_task.completed_at = datetime.now()
    if task.deadline is not None:
        db_task.deadline = datetime.fromisoformat(task.deadline) if task.deadline else None
    if task.estimated_hours is not None:
        db_task.estimated_hours = task.estimated_hours

    db.commit()
    db.refresh(db_task)
    return _format_task(db_task)


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(StudyTask).filter(StudyTask.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted", "id": task_id}


@router.get("/summary")
async def planner_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(StudyTask.id)).scalar() or 0
    pending = db.query(func.count(StudyTask.id)).filter(StudyTask.status == "pending").scalar() or 0
    in_progress = db.query(func.count(StudyTask.id)).filter(StudyTask.status == "in_progress").scalar() or 0
    completed = db.query(func.count(StudyTask.id)).filter(StudyTask.status == "completed").scalar() or 0

    upcoming = db.query(StudyTask).filter(
        StudyTask.status != "completed",
        StudyTask.deadline >= datetime.now(),
    ).order_by(StudyTask.deadline).limit(5).all()

    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
        "upcoming": [_format_task(t) for t in upcoming],
    }


def _format_task(t: StudyTask) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "subject": t.subject,
        "topic": t.topic,
        "priority": t.priority,
        "status": t.status,
        "deadline": t.deadline.isoformat() if t.deadline else None,
        "estimated_hours": t.estimated_hours,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }
