from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from backend.database.config import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500))
    file_type = Column(String(50))
    file_size = Column(Integer)
    status = Column(String(50), default="processing")
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True)
    role = Column(String(50))
    content = Column(Text)
    sources = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PyqAnalysis(Base):
    __tablename__ = "pyq_analyses"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500))
    question_count = Column(Integer, default=0)
    topics = Column(JSON)
    patterns = Column(JSON)
    clusters = Column(JSON)
    difficulty_distribution = Column(JSON)
    status = Column(String(50), default="processing")
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500))
    topic = Column(String(255))
    source_document_ids = Column(JSON)
    questions = Column(JSON)
    difficulty = Column(String(50), default="medium")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    score = Column(Float)
    total_questions = Column(Integer)
    correct_answers = Column(Integer)
    answers = Column(JSON)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())


class StudyTask(Base):
    __tablename__ = "study_tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500))
    subject = Column(String(255))
    topic = Column(String(255))
    priority = Column(String(50), default="medium")
    status = Column(String(50), default="pending")
    deadline = Column(DateTime(timezone=True), nullable=True)
    estimated_hours = Column(Float, default=1.0)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
