from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os

from backend.rag.pipeline import document_store
from backend.database.config import get_db
from backend.database.models import Document
from backend.utils.helpers import validate_file, delete_file
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    uploaded_at: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


@router.get("/", response_model=DocumentListResponse)
async def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "file_size": d.file_size,
                "status": d.status,
                "chunk_count": d.chunk_count,
                "error_message": d.error_message,
                "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
            }
            for d in docs
        ],
        "total": len(docs),
    }


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()

        upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        os.makedirs(upload_dir, exist_ok=True)
        temp_path = os.path.join(upload_dir, f"temp_{file.filename}")

        with open(temp_path, "wb") as f:
            f.write(content)

        valid, error = validate_file(temp_path)
        if not valid:
            os.remove(temp_path)
            raise HTTPException(status_code=400, detail=error)

        from backend.utils.helpers import save_uploaded_file
        final_path = save_uploaded_file(content, file.filename)
        os.remove(temp_path)

        file_type = os.path.splitext(file.filename)[1].lower().lstrip(".")
        doc = Document(
            filename=file.filename,
            file_type=file_type,
            file_size=len(content),
            status="processing",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        result = document_store.process_document(doc.id, final_path, file.filename)

        doc.status = result["status"]
        doc.chunk_count = result.get("chunk_count", 0)
        doc.error_message = result.get("error")
        if result.get("text_length"):
            doc.processed_at = datetime.now()
        db.commit()

        return DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            status=doc.status,
            chunk_count=doc.chunk_count,
            error_message=doc.error_message,
            uploaded_at=doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    document_store.remove_document(doc_id)

    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    for f in os.listdir(upload_dir):
        if doc.filename.replace(" ", "_") in f or doc.filename in f:
            delete_file(os.path.join(upload_dir, f))

    db.delete(doc)
    db.commit()

    return {"message": "Document deleted successfully", "id": doc_id}
