import os
from typing import List, Dict, Optional
# ponytail: heavy ML imports (torch/faiss) are lazy inside methods so cold start + serverless don't pay it until embeddings are actually used


class EmbeddingService:
    """Service for generating and managing text embeddings."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.model = None
        self.dimension = 384  # ponytail: true dim set on first load; 384 matches MiniLM-L6-v2

    def _load(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
        return self.model

    def embed_text(self, text: str):
        """Generate embedding for a single text."""
        import numpy as np
        embedding = self._load().encode(text, normalize_embeddings=True)
        return embedding.astype(np.float32)

    def embed_texts(self, texts: List[str]):
        """Generate embeddings for multiple texts."""
        import numpy as np
        embeddings = self._load().encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.astype(np.float32)

    def similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""
        import numpy as np
        emb1 = self.embed_text(text1)
        emb2 = self.embed_text(text2)
        return float(np.dot(emb1, emb2))


class VectorStore:
    """FAISS-based vector store for document retrieval."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = None
        self.documents: List[Dict] = []

    def add_documents(self, chunks: List[Dict], embeddings):
        """Add document chunks with their embeddings to the index."""
        import faiss
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.dimension)

        self.index.add(embeddings)
        self.documents.extend(chunks)

    def search(self, query_embedding, top_k: int = 5) -> List[Dict]:
        """Search for most similar documents."""
        if self.index is None or self.index.ntotal == 0:
            return []

        top_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(
            query_embedding.reshape(1, -1), top_k
        )

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc["score"] = float(score)
                results.append(doc)

        return results

    def clear(self):
        """Clear all documents from the store."""
        self.index = None
        self.documents = []

    def to_dict(self) -> Dict:
        """Serialize the store state."""
        return {
            "documents": self.documents,
            "dimension": self.dimension,
            "count": len(self.documents)
        }
