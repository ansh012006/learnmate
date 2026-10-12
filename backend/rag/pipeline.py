import os
from typing import List, Dict, Optional, Tuple
from backend.rag.embeddings import EmbeddingService, VectorStore
from backend.services.llm_service import llm_service
from backend.utils.helpers import extract_text_from_file, clean_text, chunk_text


class DocumentStore:
    """Manages document processing, embeddings, and retrieval."""

    def __init__(self, upload_dir: str = None):
        self.upload_dir = upload_dir or os.getenv("UPLOAD_DIR", "./uploads")
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore(dimension=self.embedding_service.dimension)
        self.documents: Dict[int, Dict] = {}

    def process_document(self, doc_id: int, file_path: str, filename: str) -> Dict:
        """Process an uploaded document: extract, chunk, embed."""
        result = {
            "id": doc_id,
            "status": "processing",
            "chunk_count": 0,
            "error": None,
        }

        try:
            # Validate file
            from backend.utils.helpers import validate_file
            valid, error = validate_file(file_path)
            if not valid:
                result["status"] = "error"
                result["error"] = error
                return result

            # Extract text
            text, error = extract_text_from_file(file_path)
            if error:
                result["status"] = "error"
                result["error"] = error
                return result

            # Clean and chunk
            text = clean_text(text)
            if len(text) < 50:
                result["status"] = "error"
                result["error"] = "Document contains too little text to process."
                return result

            chunks = chunk_text(text)
            if not chunks:
                result["status"] = "error"
                result["error"] = "Could not split document into chunks."
                return result

            # Generate embeddings
            texts = [c["text"] for c in chunks]
            embeddings = self.embedding_service.embed_texts(texts)

            # Add metadata
            for i, chunk in enumerate(chunks):
                chunk["doc_id"] = doc_id
                chunk["source"] = filename
                chunk["chunk_id"] = i

            # Store in vector DB
            self.vector_store.add_documents(chunks, embeddings)

            result["status"] = "ready"
            result["chunk_count"] = len(chunks)
            result["text_length"] = len(text)

            self.documents[doc_id] = {
                "id": doc_id,
                "filename": filename,
                "file_path": file_path,
                "chunk_count": len(chunks),
                "text_length": len(text),
                "status": "ready",
            }

            return result

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            return result

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant document chunks for a query."""
        if self.vector_store.index is None or self.vector_store.index.ntotal == 0:
            return []

        query_embedding = self.embedding_service.embed_text(query)
        results = self.vector_store.search(query_embedding, top_k=top_k)

        # Filter by relevance threshold
        return [r for r in results if r.get("score", 0) > 0.3]

    def remove_document(self, doc_id: int):
        """Remove a document from the store."""
        if doc_id in self.documents:
            file_path = self.documents[doc_id].get("file_path")
            if file_path:
                from backend.utils.helpers import delete_file
                delete_file(file_path)
            del self.documents[doc_id]

        # Rebuild vector store without this document
        if self.vector_store.documents:
            remaining = [d for d in self.vector_store.documents if d.get("doc_id") != doc_id]
            if remaining:
                self.vector_store.clear()
                texts = [d["text"] for d in remaining]
                embeddings = self.embedding_service.embed_texts(texts)
                self.vector_store.add_documents(remaining, embeddings)

    def query_with_rag(self, question: str, top_k: int = 5) -> Tuple[str, List[Dict]]:
        """Full RAG pipeline: retrieve relevant docs and generate answer."""
        relevant_docs = self.retrieve(question, top_k=top_k)

        if not relevant_docs:
            return (
                "I couldn't find relevant information in your uploaded documents. "
                "Try uploading your study materials first, or ask a general question.",
                []
            )

        context_docs = [
            {"source": d.get("source", ""), "text": d["text"]}
            for d in relevant_docs
        ]

        result = llm_service.chat(question, context_docs=context_docs)
        return result.get("response", ""), context_docs

    def get_context_for_quiz(self, topic: str, max_chunks: int = 3) -> str:
        """Get relevant context for quiz generation."""
        docs = self.retrieve(topic, top_k=max_chunks)
        if not docs:
            return ""
        return "\n\n".join([d["text"] for d in docs])


# Global document store instance
document_store = DocumentStore()
