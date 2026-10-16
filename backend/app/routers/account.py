from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select

from app.dependencies import AuthContext, CurrentAuth, DbSession, require_roles
from app.models import Complaint, Notification
from app.schemas import FeedbackCreate, NotificationRead
from app.serializers import can_access_complaint

router = APIRouter(tags=["Notifications and feedback"])


@router.get("/notifications", response_model=dict)
def list_notifications(db: DbSession, auth: CurrentAuth, page: int = 1, page_size: int = 50):
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(status_code=422, detail="page must be positive and page_size must be between 1 and 100")
    query = select(Notification).where(Notification.user_id == auth.user.id).order_by(Notification.created_at.desc())
    rows = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    unread = db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == auth.user.id, Notification.is_read.is_(False))) or 0
    items = [NotificationRead(id=item.id, complaint_id=item.complaint_id, title=item.title, message=item.message, notification_type=item.notification_type, is_read=item.is_read, created_at=item.created_at).model_dump(mode="json") for item in rows]
    return {"data": items, "meta": {"unread": unread}}


@router.patch("/notifications/read-all", response_model=dict)
def mark_all_notifications_read(db: DbSession, auth: CurrentAuth):
    rows = db.scalars(select(Notification).where(Notification.user_id == auth.user.id, Notification.is_read.is_(False))).all()
    for item in rows:
        item.is_read = True
    db.commit()
    return {"data": {"updated": len(rows)}}


@router.patch("/notifications/{notification_id}/read", response_model=dict)
def mark_notification_read(notification_id: int, db: DbSession, auth: CurrentAuth):
    notification = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == auth.user.id))
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    return {"data": {"id": notification.id, "is_read": notification.is_read}}


@router.post("/feedback", response_model=dict, status_code=status.HTTP_201_CREATED)
def submit_feedback(payload: FeedbackCreate, db: DbSession, auth: AuthContext = Depends(require_roles("citizen"))):
    complaint = None
    if payload.complaint_id:
        complaint = db.get(Complaint, payload.complaint_id)
        if complaint is None or not can_access_complaint(db, auth.user, complaint):
            raise HTTPException(status_code=404, detail="Complaint not found")
    from app.models import CitizenFeedback

    feedback = CitizenFeedback(citizen_id=auth.user.id, complaint_id=payload.complaint_id, rating=payload.rating, comments=payload.comments.strip() if payload.comments else None)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {"data": {"id": feedback.id, "complaint_id": feedback.complaint_id, "rating": feedback.rating, "comments": feedback.comments, "created_at": feedback.created_at}}
