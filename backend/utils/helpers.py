import os
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".doc"}

os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """Validate uploaded file for type and size."""
    ext = Path(file_path).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

    size = os.path.getsize(file_path)
    if size > MAX_UPLOAD_SIZE:
        return False, f"File too large ({size / 1024 / 1024:.1f}MB). Max: 50MB"

    return True, None


def extract_text_from_file(file_path: str) -> Tuple[str, Optional[str]]:
    """Extract text from PDF, TXT, or DOCX files."""
    ext = Path(file_path).suffix.lower()

    try:
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(), None

        elif ext in (".pdf",):
            return extract_pdf_text(file_path)

        elif ext in (".docx", ".doc"):
            return extract_docx_text(file_path)

        else:
            return "", f"Unsupported file type: {ext}"

    except Exception as e:
        return "", f"Error extracting text: {str(e)}"


def extract_pdf_text(file_path: str) -> Tuple[str, Optional[str]]:
    """Extract text from PDF with fallback handling."""
    text_parts = []

    # Try pypdf first
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        if text_parts:
            return "\n\n".join(text_parts), None
    except Exception:
        pass

    # Fallback to PyPDF2
    try:
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        if text_parts:
            return "\n\n".join(text_parts), None
    except Exception:
        pass

    return "", "Could not extract text. The PDF may be scanned (image-based) or password-protected."


def extract_docx_text(file_path: str) -> Tuple[str, Optional[str]]:
    """Extract text from DOCX files."""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs), None
    except Exception as e:
        return "", f"Error reading DOCX: {str(e)}"


def clean_text(text: str) -> str:
    """Clean extracted text for processing."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
    """Split text into overlapping chunks for RAG."""
    if not text or not text.strip():
        return []

    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            for sep in ['. ', '.\n', '! ', '? ', '\n\n']:
                last_sep = text.rfind(sep, start, end)
                if last_sep > start + chunk_size // 2:
                    end = last_sep + len(sep)
                    break

        chunk_text = text[start:end].strip()
        if chunk_text and len(chunk_text) > 50:
            chunks.append({
                "index": chunk_index,
                "text": chunk_text,
                "char_count": len(chunk_text),
                "start_char": start,
            })
            chunk_index += 1

        if end >= len(text):
            break
        start = end - overlap

    return chunks


def save_uploaded_file(file_content: bytes, filename: str) -> str:
    """Save uploaded file to disk with safe name."""
    ext = Path(filename).suffix.lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', Path(filename).stem)
    new_filename = f"{timestamp}_{safe_name}{ext}"
    file_path = os.path.join(UPLOAD_DIR, new_filename)

    with open(file_path, "wb") as f:
        f.write(file_content)

    return file_path


def delete_file(file_path: str):
    """Delete a file from disk."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass


def extract_questions_from_pdf(file_path: str) -> List[str]:
    """Extract individual questions from a PDF (for PYQ analysis)."""
    text, error = extract_text_from_file(file_path)
    if error or not text:
        return []

    text = clean_text(text)
    questions = []

    # Split by question markers
    lines = text.split('\n')
    current_q = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if re.match(r'^(\d+\.?\s|Q\.?\d*\.?\s|Question\s+\d+)', line, re.IGNORECASE):
            if current_q:
                questions.append(' '.join(current_q))
            current_q = [line]
        elif re.match(r'^(a\)|b\)|c\)|d\)|i\)|ii\)|iii\)|iv\))', line, re.IGNORECASE):
            if current_q:
                current_q.append(line)
        else:
            current_q.append(line)

    if current_q:
        questions.append(' '.join(current_q))

    return [q for q in questions if len(q) > 20]
