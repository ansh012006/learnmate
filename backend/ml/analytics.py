from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Tuple


def compute_tfidf_similarity(texts: List[str]) -> np.ndarray:
    """Compute TF-IDF cosine similarity matrix between texts."""
    if len(texts) < 2:
        return np.array([[1.0]])

    vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    return cosine_similarity(tfidf_matrix)


def find_similar_questions(questions: List[str], threshold: float = 0.5) -> List[Tuple[int, int, float]]:
    """Find pairs of semantically similar questions."""
    if len(questions) < 2:
        return []

    sim_matrix = compute_tfidf_similarity(questions)
    similar_pairs = []

    for i in range(len(questions)):
        for j in range(i + 1, len(questions)):
            if sim_matrix[i][j] >= threshold:
                similar_pairs.append((i, j, float(sim_matrix[i][j])))

    similar_pairs.sort(key=lambda x: x[2], reverse=True)
    return similar_pairs
