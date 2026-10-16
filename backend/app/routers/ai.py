from fastapi import APIRouter
from sqlalchemy import select

from app.ai import categorize, recommend_priority
from app.dependencies import CurrentAuth, DbSession
from app.models import Complaint
from app.routers.complaints import _duplicate_candidates
from app.schemas import AIRequest
from app.serializers import visible_complaints

router = APIRouter(prefix="/ai", tags=["AI recommendations"])


@router.post("/analyze", response_model=dict)
def analyze_complaint(payload: AIRequest, db: DbSession, auth: CurrentAuth):
    category_result = categorize(payload.title, payload.description)
    priority_result = recommend_priority(payload.severity, payload.safety_impact, payload.complaint_age_days)
    text = f"{payload.title}. {payload.description}"
    duplicates = _duplicate_candidates(db, text)
    if auth.user.role != "admin":
        duplicates = [{"similarity": match["similarity"]} for match in duplicates]
    return {"data": {"category": category_result, "priority": priority_result, "possible_duplicates": duplicates, "review_required": True}}


@router.get("/categories", response_model=dict)
def categories(db: DbSession, auth: CurrentAuth):
    names = ["Roads", "Garbage", "Water Supply", "Drainage", "Streetlights"]
    query = visible_complaints(db, auth.user)
    scoped_items = db.scalars(query).all()
    counts: dict[str, int] = {}
    for item in scoped_items:
        counts[item.category] = counts.get(item.category, 0) + 1
    icons = {"Roads": "Construction", "Garbage": "Trash2", "Water Supply": "Droplets", "Drainage": "Waves", "Streetlights": "Lamp"}
    return {"data": [{"name": name, "icon": icons[name], "count": counts.get(name, 0)} for name in names]}
