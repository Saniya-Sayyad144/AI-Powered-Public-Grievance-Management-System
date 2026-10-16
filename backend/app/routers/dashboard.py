from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter
from sqlalchemy import func, select

from app.dependencies import CurrentAuth, DbSession
from app.models import CitizenFeedback, Complaint, ComplaintStatusHistory
from app.serializers import visible_complaints

router = APIRouter(prefix="/dashboard", tags=["Dashboard analytics"])


@router.get("/stats", response_model=dict)
def dashboard_stats(db: DbSession, auth: CurrentAuth):
    scoped = visible_complaints(db, auth.user)
    rows = db.scalars(scoped).all()
    total = len(rows)
    by_status: dict[str, int] = {}
    by_category: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    for item in rows:
        by_status[item.status] = by_status.get(item.status, 0) + 1
        by_category[item.category] = by_category.get(item.category, 0) + 1
        by_priority[item.priority] = by_priority.get(item.priority, 0) + 1
    resolved_at = []
    if rows:
        resolved_at = [
            event.created_at
            for event in db.scalars(select(ComplaintStatusHistory).where(
                ComplaintStatusHistory.complaint_id.in_([item.id for item in rows]),
                ComplaintStatusHistory.new_status == "Resolved",
            ))
        ]

    today = datetime.now(timezone.utc).date()
    weekly = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        start = datetime.combine(day, time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        filed = sum(1 for item in rows if start <= item.created_at.replace(tzinfo=timezone.utc) < end)
        resolved = sum(1 for resolved_date in resolved_at if start <= resolved_date.replace(tzinfo=timezone.utc) < end)
        weekly.append({"day": day.strftime("%a"), "date": day.isoformat(), "filed": filed, "resolved": resolved})

    feedback_query = select(func.avg(CitizenFeedback.rating))
    if auth.user.role == "citizen":
        feedback_query = feedback_query.where(CitizenFeedback.citizen_id == auth.user.id)
    satisfaction = db.scalar(feedback_query)
    return {"data": {
        "total": total,
        "open": sum(count for name, count in by_status.items() if name != "Resolved"),
        "in_progress": by_status.get("In Progress", 0),
        "resolved": by_status.get("Resolved", 0),
        "critical": by_priority.get("Critical", 0),
        "needs_attention": by_status.get("Under Review", 0) + by_status.get("Submitted", 0),
        "by_status": by_status,
        "by_category": [{"name": name, "value": count} for name, count in sorted(by_category.items())],
        "by_priority": by_priority,
        "weekly": weekly,
        "satisfaction": round(float(satisfaction), 1) if satisfaction is not None else None,
    }}
