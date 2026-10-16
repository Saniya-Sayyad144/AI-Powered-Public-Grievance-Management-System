from datetime import datetime, timezone

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity

CATEGORY_EXAMPLES = {
    "Roads": ["pothole on road", "broken pavement and damaged street", "traffic signal road damage", "unsafe road surface", "cracked bridge or footpath"],
    "Garbage": ["garbage not collected", "overflowing trash bin", "illegal dumping waste", "street litter and bad smell", "municipal sanitation collection missed"],
    "Water Supply": ["no water supply", "water pipe leaking", "contaminated drinking water", "low pressure water connection", "brown water from tap"],
    "Drainage": ["blocked storm drain", "sewage overflow", "street flooding after rain", "drain clogged with debris", "open drainage channel"],
    "Streetlights": ["street light not working", "broken lamp post", "dark road at night", "public area lighting outage", "damaged electrical streetlight"],
}

_training_texts = [text for category, examples in CATEGORY_EXAMPLES.items() for text in examples]
_training_labels = [category for category, examples in CATEGORY_EXAMPLES.items() for _ in examples]
_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
_training_matrix = _vectorizer.fit_transform(_training_texts)
_classifier = LogisticRegression(max_iter=500, random_state=7).fit(_training_matrix, _training_labels)


def categorize(title: str, description: str) -> dict[str, object]:
    text = f"{title}. {description}"
    scores = _classifier.predict_proba(_vectorizer.transform([text]))[0]
    best_index = int(scores.argmax())
    return {
        "category": str(_classifier.classes_[best_index]),
        "confidence": round(float(scores[best_index]), 4),
        "explanation": "Calculated from TF-IDF features and a trained logistic-regression model using the included civic issue examples.",
    }


def find_duplicates(text: str, candidates: list[tuple[str, str]], threshold: float = 0.36) -> list[dict[str, object]]:
    if not candidates:
        return []
    corpus = [text, *(candidate_text for _, candidate_text in candidates)]
    try:
        matrix = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True).fit_transform(corpus)
    except ValueError:
        return []
    scores = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    matches = [
        {"complaint_id": complaint_id, "similarity": round(float(score), 4)}
        for (complaint_id, _), score in zip(candidates, scores, strict=True)
        if float(score) >= threshold
    ]
    return sorted(matches, key=lambda item: float(item["similarity"]), reverse=True)


def recommend_priority(severity: int, safety_impact: bool, complaint_age_days: int, created_at: datetime | None = None) -> dict[str, object]:
    score = severity * 2 + (3 if safety_impact else 0) + min(complaint_age_days // 3, 4)
    if score >= 12:
        priority = "Critical"
    elif score >= 9:
        priority = "High"
    elif score >= 5:
        priority = "Medium"
    else:
        priority = "Low"
    factors = [f"severity {severity}/5"]
    if safety_impact:
        factors.append("reported safety impact")
    if complaint_age_days:
        factors.append(f"{complaint_age_days} days old")
    return {
        "priority": priority,
        "score": score,
        "explanation": "Rule-based recommendation from " + ", ".join(factors) + ". A city reviewer must confirm priority.",
        "calculated_at": (created_at or datetime.now(timezone.utc)).isoformat(),
    }
