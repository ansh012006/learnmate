from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

from backend.services.llm_service import llm_service
from backend.rag.pipeline import document_store
from backend.database.config import get_db
from backend.database.models import ChatMessage
from sqlalchemy.orm import Session

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = "default"
    use_documents: bool = False


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: Optional[List[Dict]] = None
    error: bool = False


@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        user_msg = ChatMessage(
            session_id=request.session_id,
            role="user",
            content=request.message,
        )
        db.add(user_msg)

        context_docs = []
        sources = []

        if request.use_documents:
            relevant_docs = document_store.retrieve(request.message, top_k=3)
            if relevant_docs:
                context_docs = [
                    {"source": d.get("source", ""), "text": d["text"]}
                    for d in relevant_docs
                ]
                sources = [
                    {"source": d.get("source", ""), "score": d.get("score", 0)}
                    for d in relevant_docs
                ]

        result = llm_service.chat(request.message, request.session_id, context_docs)
        response_text = result.get("response", "Sorry, I couldn't generate a response.")

        assistant_msg = ChatMessage(
            session_id=request.session_id,
            role="assistant",
            content=response_text,
            sources=sources if sources else None,
        )
        db.add(assistant_msg)
        db.commit()

        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            sources=sources if sources else None,
            error=result.get("error", False),
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_chat(session_id: str = "default"):
    llm_service.clear_context(session_id)
    return {"message": "Chat history cleared", "session_id": session_id}


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).limit(50).all()

    return {
        "session_id": session_id,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "sources": m.sources,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ]
    }
