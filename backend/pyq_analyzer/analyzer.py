from typing import List, Dict
from backend.services.llm_service import llm_service
from backend.utils.helpers import extract_questions_from_pdf, clean_text


def analyze_pyq_document(file_path: str, filename: str) -> Dict:
    """Analyze a previous year question paper."""
    result = {
        "filename": filename,
        "status": "processing",
        "question_count": 0,
        "topics": [],
        "patterns": {},
        "clusters": [],
        "difficulty_distribution": {},
    }

    try:
        # Extract questions
        questions = extract_questions_from_pdf(file_path)
        if not questions:
            result["status"] = "error"
            result["error"] = "Could not extract questions from the PDF."
            return result

        result["question_count"] = len(questions)

        # Combine all questions for analysis
        questions_text = "\n\n".join(questions[:50])  # Limit for token usage
        cleaned_text = clean_text(questions_text)

        # AI-powered analysis
        analysis = llm_service.analyze_pyq_topics(cleaned_text)
        result["topics"] = analysis.get("topics", [])
        result["patterns"] = analysis.get("patterns", {})
        result["important_topics"] = analysis.get("important_topics", [])

        # Pattern analysis
        patterns = _analyze_question_patterns(questions)
        result["patterns"] = {**result["patterns"], **patterns}

        # Topic extraction using keyword frequency
        topic_freq = _extract_topic_keywords(questions)
        result["topics"] = _merge_topics(result.get("topics", []), topic_freq)

        # Difficulty estimation (heuristic)
        result["difficulty_distribution"] = _estimate_difficulty(questions)

        # Semantic clustering of questions
        result["clusters"] = _cluster_questions(questions)

        result["status"] = "completed"
        return result

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        return result


def _analyze_question_patterns(questions: List[str]) -> Dict:
    """Analyze the patterns/types of questions."""
    patterns = {
        "define": 0,
        "explain": 0,
        "compare": 0,
        "differentiate": 0,
        "short_answer": 0,
        "long_answer": 0,
        "numerical": 0,
        "diagram": 0,
    }

    keywords = {
        "define": ["define", "what is", "what are", "meaning of", "definition"],
        "explain": ["explain", "describe", "elaborate", "discuss", "write note on"],
        "compare": ["compare", "comparison", "distinguish between", "similarities"],
        "differentiate": ["differentiate", "difference between", "contrast"],
        "short_answer": ["short answer", "brief", "mention", "list", "name"],
        "long_answer": ["long answer", "essay", "detailed", "in detail", "elucidate"],
        "numerical": ["calculate", "solve", "find the value", "compute", "numerical"],
        "diagram": ["draw", "diagram", "label", "sketch"],
    }

    for q in questions:
        q_lower = q.lower()
        for pattern, words in keywords.items():
            if any(word in q_lower for word in words):
                patterns[pattern] += 1

    return patterns


def _extract_topic_keywords(questions: List[str], top_n: int = 10) -> List[Dict]:
    """Extract frequent topic keywords from questions."""
    from collections import Counter
    import re

    # Common stopwords
    stopwords = set([
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "into", "through",
        "during", "before", "after", "above", "below", "between", "out", "off",
        "over", "under", "again", "further", "then", "once", "here", "there",
        "when", "where", "why", "how", "all", "both", "each", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only", "own",
        "same", "so", "than", "too", "very", "just", "because", "but", "and",
        "or", "if", "while", "about", "up", "what", "which", "who", "whom",
        "this", "that", "these", "those", "question", "answer", "marks",
        "long", "short", "note", "brief", "explain", "describe", "write",
        "draw", "state", "mention", "list", "give", "find", "calculate",
        "following", "following", "based", "using", "related",
    ])

    words = []
    for q in questions:
        tokens = re.findall(r'\b[a-zA-Z]{3,}\b', q.lower())
        words.extend([w for w in tokens if w not in stopwords])

    word_freq = Counter(words)
    top_words = word_freq.most_common(top_n)

    topics = []
    for word, count in top_words:
        if count > 1:
            matching_qs = [q for q in questions if word in q.lower()][:3]
            topics.append({
                "name": word.title(),
                "count": count,
                "questions": matching_qs,
                "frequency_percent": round(count / len(questions) * 100, 1),
            })

    return topics


def _estimate_difficulty(questions: List[str]) -> Dict:
    """Heuristic difficulty estimation."""
    difficulty = {"easy": 0, "medium": 0, "hard": 0}
    total = len(questions)

    for q in questions:
        q_len = len(q.split())
        has_complex = any(w in q.lower() for w in
                         ["analyze", "evaluate", "critically", "compare",
                          "differentiate", "relationship", "justify"])

        if has_complex or q_len > 30:
            difficulty["hard"] += 1
        elif q_len > 15:
            difficulty["medium"] += 1
        else:
            difficulty["easy"] += 1

    return {k: {"count": v, "percent": round(v / total * 100, 1) if total else 0}
            for k, v in difficulty.items()}


def _cluster_questions(questions: List[str], n_clusters: int = 5) -> List[Dict]:
    """Cluster questions semantically using embeddings."""
    if len(questions) < 2:
        return []

    try:
        from backend.rag.embeddings import EmbeddingService
        from sklearn.cluster import KMeans

        embedder = EmbeddingService()
        embeddings = embedder.embed_texts(questions)

        n_clusters = min(n_clusters, len(questions))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        labels = kmeans.fit_predict(embeddings)

        clusters = []
        for i in range(n_clusters):
            cluster_qs = [questions[j] for j, label in enumerate(labels) if label == i]
            if cluster_qs:
                # Find the question closest to centroid as representative
                centroid = kmeans.cluster_centers_[i]
                distances = [
                    float(np.linalg.norm(embeddings[j] - centroid))
                    for j in range(len(questions)) if labels[j] == i
                ]
                min_dist_idx = distances.index(min(distances))
                representative = questions[
                    [j for j, label in enumerate(labels) if label == i][min_dist_idx]
                ]

                clusters.append({
                    "id": i + 1,
                    "count": len(cluster_qs),
                    "representative_question": representative[:200],
                    "questions": cluster_qs[:5],
                })

        return clusters

    except Exception as e:
        print(f"Clustering error: {e}")
        return []


def _merge_topics(ai_topics: List[Dict], keyword_topics: List[Dict]) -> List[Dict]:
    """Merge AI-identified and keyword-extracted topics."""
    seen = set()
    merged = []

    for topic in ai_topics + keyword_topics:
        name = topic.get("name", "").lower()
        if name not in seen:
            seen.add(name)
            merged.append(topic)

    merged.sort(key=lambda x: x.get("count", 0), reverse=True)
    return merged
