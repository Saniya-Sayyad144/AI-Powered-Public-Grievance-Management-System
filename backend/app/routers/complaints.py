import csv
import io
import logging
import re
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from app.ai import categorize, find_duplicates, recommend_priority
from app.config import settings
from app.dependencies import AuthContext, CurrentAuth, DbSession, require_roles
from app.models import Complaint, ComplaintAssignment, ComplaintAttachment, ComplaintComment, ComplaintDuplicate, ComplaintStatusHistory, Department, Notification, User
from app.schemas import AssignmentCreate, CommentCreate, ComplaintCreate, ComplaintUpdate, StatusUpdate
from app.serializers import can_access_complaint, complaint_data, visible_complaints

router = APIRouter(tags=["Complaints"])
logger = logging.getLogger(__name__)
CATEGORY_DEPARTMENTS = {
    "Roads": "Public Works",
    "Garbage": "Sanitation",
    "Water Supply": "Water Works",
    "Drainage": "Drainage",
    "Streetlights": "Electrical",
}
VALID_CATEGORIES = set(CATEGORY_DEPARTMENTS)
NEXT_STATUSES = {
    "Submitted": {"Under Review"},
    "Under Review": {"Assigned"},
    "Assigned": {"In Progress"},
    "In Progress": {"Resolved"},
    "Resolved": set(),
}


def _accessible_complaint(db: Session, auth: AuthContext, complaint_id: str) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None or not can_access_complaint(db, auth.user, complaint):
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


def _notify(db: Session, user_id: int, complaint_id: str, title: str, message: str, notification_type: str) -> None:
    db.add(Notification(user_id=user_id, complaint_id=complaint_id, title=title, message=message, notification_type=notification_type))


def _change_status(db: Session, complaint: Complaint, new_status: str, actor: User, note: str | None = None) -> None:
    previous_status = complaint.status
    if new_status not in NEXT_STATUSES.get(previous_status, set()):
        raise HTTPException(status_code=409, detail=f"Status cannot move from {previous_status} to {new_status}")
    complaint.status = new_status
    db.add(ComplaintStatusHistory(complaint_id=complaint.id, previous_status=previous_status, new_status=new_status, changed_by_id=actor.id, note=note))


def _text_for(complaint: Complaint) -> str:
    return f"{complaint.title}. {complaint.description}"


def _duplicate_candidates(db: Session, text: str, exclude_id: str | None = None):
    scope = select(Complaint).where(Complaint.id != (exclude_id or ""))
    matches = db.scalars(scope.order_by(Complaint.created_at.desc()).limit(300)).all()
    candidate_data = [(item.id, _text_for(item)) for item in matches]
    return find_duplicates(text, candidate_data)


def _priority_for(title: str, description: str, days_old: int = 0):
    text = f"{title} {description}".casefold()
    severe_terms = ("contaminat", "sewage", "electroc", "exposed wire", "open manhole", "collapse", "injur", "fire", "accident")
    safety_terms = ("school", "child", "unsafe", "danger", "traffic", "flood", "contaminat", "sewage", "electroc", "injur", "fire", "accident")
    severity = 5 if any(term in text for term in severe_terms) else 4 if any(term in text for term in safety_terms) else 3 if any(term in text for term in ("urgent", "overflow", "blocked", "not working")) else 2
    return recommend_priority(severity, any(term in text for term in safety_terms), days_old)


def _complaint_id(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(hashtext('civicpulse:complaint-id'))"))
    existing_ids = db.scalars(select(Complaint.id).where(Complaint.id.like(f"CP-{year}-%"))).all()
    numbers = [int(value.rsplit("-", 1)[-1]) for value in existing_ids if value.rsplit("-", 1)[-1].isdigit()]
    return f"CP-{year}-{max(numbers, default=0) + 1:04d}"


@router.get("/complaints", response_model=dict)
def list_complaints(
    db: DbSession,
    auth: CurrentAuth,
    q: str | None = None,
    complaint_status: str | None = Query(default=None, alias="status"),
    category: str | None = None,
    priority: str | None = None,
    department_id: int | None = None,
    officer_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: str = Query(default="created_at", pattern="^(created_at|status|priority|category)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    if date_from and date_to and date_to < date_from:
        raise HTTPException(status_code=422, detail="date_to must be on or after date_from")
    query = visible_complaints(db, auth.user)
    if q:
        term = f"%{q.strip()}%"
        query = query.where(or_(Complaint.id.ilike(term), Complaint.title.ilike(term), Complaint.description.ilike(term), Complaint.location.ilike(term), Complaint.category.ilike(term)))
    if complaint_status:
        query = query.where(Complaint.status == complaint_status)
    if category:
        query = query.where(Complaint.category == category)
    if priority:
        query = query.where(Complaint.priority == priority)
    if department_id:
        query = query.where(Complaint.department_id == department_id)
    if officer_id is not None:
        if auth.user.role != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can filter by officer")
        query = query.join(ComplaintAssignment).where(
            ComplaintAssignment.officer_id == officer_id,
            ComplaintAssignment.is_active.is_(True),
        )
    if date_from:
        query = query.where(Complaint.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
    if date_to:
        query = query.where(Complaint.created_at <= datetime.combine(date_to, time.max, tzinfo=timezone.utc))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    sort_column = getattr(Complaint, sort_by)
    query = query.order_by(sort_column.asc() if order == "asc" else sort_column.desc(), Complaint.id.asc())
    rows = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    items = [complaint_data(db, item, auth.user, detailed=False) for item in rows]
    return {"data": items, "meta": {"page": page, "page_size": page_size, "total": total, "pages": (total + page_size - 1) // page_size}}


@router.post("/complaints", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_complaint(payload: ComplaintCreate, db: DbSession, auth: AuthContext = Depends(require_roles("citizen"))):
    title = payload.title.strip()
    description = payload.description.strip()
    recommendation = categorize(title, description)
    category = payload.category or str(recommendation["category"])
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Category must be one of: {', '.join(sorted(VALID_CATEGORIES))}")
    priority = _priority_for(title, description)
    department = db.scalar(select(Department).where(Department.name == CATEGORY_DEPARTMENTS[category]))
    ai_reason = f"AI suggested {recommendation['category']} with {float(recommendation['confidence']):.0%} model confidence. {priority['explanation']} Staff should confirm category and priority."
    complaint = Complaint(
        id=_complaint_id(db), citizen_id=auth.user.id, title=title, description=description,
        category=category, status="Submitted", priority=str(priority["priority"]), location=payload.location.strip(),
        latitude=payload.latitude, longitude=payload.longitude, department_id=department.id if department else None, ai_reason=ai_reason,
    )
    db.add(complaint)
    db.flush()
    db.add(ComplaintStatusHistory(complaint_id=complaint.id, previous_status=None, new_status="Submitted", changed_by_id=auth.user.id, note="Complaint submitted by citizen"))
    _notify(db, auth.user.id, complaint.id, "Complaint received", f"Complaint {complaint.id} was submitted successfully", "complaint_submitted")
    admin_ids = db.scalars(select(User.id).where(User.role == "admin", User.is_active.is_(True))).all()
    for admin_id in admin_ids:
        _notify(db, admin_id, complaint.id, "New complaint", f"Complaint {complaint.id} is ready for review", "new_complaint")
    candidates = _duplicate_candidates(db, _text_for(complaint), exclude_id=complaint.id)
    for match in candidates:
        first, second = sorted((complaint.id, str(match["complaint_id"])))
        db.add(ComplaintDuplicate(complaint_id=first, possible_duplicate_id=second, similarity=float(match["similarity"])))
    db.commit()
    db.refresh(complaint)
    logger.info("Complaint created: complaint_id=%s citizen_id=%s", complaint.id, auth.user.id)
    return {"data": complaint_data(db, complaint, auth.user)}


@router.get("/complaints/export.csv")
def export_complaints_csv(db: DbSession, auth: CurrentAuth):
    rows = db.scalars(visible_complaints(db, auth.user).order_by(Complaint.created_at.desc())).all()
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["ID", "Title", "Description", "Category", "Status", "Priority", "Location", "Department", "Citizen", "Officer", "Created at"])
    for item in rows:
        data = complaint_data(db, item, auth.user, detailed=False)
        writer.writerow([data["id"], data["title"], data["description"], data["category"], data["status"], data["priority"], data["location"], data["department"], data["citizen"], data["officer"], data["date"].isoformat()])
    filename = f"civicpulse-complaints-{date.today().isoformat()}.csv"
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/complaints/{complaint_id}/track", response_model=dict)
def track_complaint(complaint_id: str, db: DbSession, auth: CurrentAuth):
    complaint = _accessible_complaint(db, auth, complaint_id)
    data = complaint_data(db, complaint, auth.user)
    return {"data": {key: data[key] for key in ("id", "title", "category", "status", "date", "history")}}


@router.get("/complaints/{complaint_id}", response_model=dict)
def get_complaint(complaint_id: str, db: DbSession, auth: CurrentAuth):
    complaint = _accessible_complaint(db, auth, complaint_id)
    return {"data": complaint_data(db, complaint, auth.user)}


@router.patch("/complaints/{complaint_id}", response_model=dict)
def update_complaint(complaint_id: str, payload: ComplaintUpdate, db: DbSession, auth: CurrentAuth):
    complaint = _accessible_complaint(db, auth, complaint_id)
    if auth.user.role == "officer":
        raise HTTPException(status_code=403, detail="Officers cannot edit citizen-submitted complaint details")
    if auth.user.role == "citizen" and complaint.status not in {"Submitted", "Under Review"}:
        raise HTTPException(status_code=409, detail="Complaint details can no longer be changed")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(complaint, key, value.strip() if isinstance(value, str) else value)
    complaint.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(complaint)
    return {"data": complaint_data(db, complaint, auth.user)}


@router.post("/complaints/{complaint_id}/assign", response_model=dict)
def assign_complaint(complaint_id: str, payload: AssignmentCreate, db: DbSession, auth: AuthContext = Depends(require_roles("admin"))):
    complaint = _accessible_complaint(db, auth, complaint_id)
    department = db.get(Department, payload.department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    officer = db.get(User, payload.officer_id) if payload.officer_id is not None else None
    if payload.officer_id is not None and (officer is None or officer.role != "officer" or not officer.is_active):
        raise HTTPException(status_code=422, detail="Selected user is not an active officer")
    if officer and officer.department_id != department.id:
        raise HTTPException(status_code=422, detail="Officer does not belong to the selected department")
    active_assignments = [assignment for assignment in complaint.assignments if assignment.is_active]
    if any(
        assignment.department_id == department.id and assignment.officer_id == payload.officer_id
        for assignment in active_assignments
    ):
        return {"data": complaint_data(db, complaint, auth.user)}
    previous_officer_ids = {assignment.officer_id for assignment in active_assignments if assignment.officer_id is not None}
    for assignment in active_assignments:
        if assignment.is_active:
            assignment.is_active = False
    assignment = ComplaintAssignment(complaint_id=complaint.id, department_id=department.id, officer_id=officer.id if officer else None, assigned_by_id=auth.user.id, is_active=True)
    complaint.department_id = department.id
    db.add(assignment)
    if complaint.status == "Submitted":
        _change_status(db, complaint, "Under Review", auth.user, "Initial review completed")
    if complaint.status == "Under Review":
        _change_status(db, complaint, "Assigned", auth.user, f"Assigned to {department.name}")
    message = f"Complaint {complaint.id} was assigned to {department.name}"
    _notify(db, complaint.citizen_id, complaint.id, "Complaint assigned", message, "complaint_assigned")
    if officer:
        for previous_officer_id in previous_officer_ids - {officer.id}:
            _notify(db, previous_officer_id, complaint.id, "Complaint reassigned", f"Complaint {complaint.id} is no longer assigned to you", "complaint_reassigned")
    if officer:
        _notify(db, officer.id, complaint.id, "Complaint assigned to you", f"Complaint {complaint.id} was assigned to you", "complaint_assigned")
    db.commit()
    db.refresh(complaint)
    return {"data": complaint_data(db, complaint, auth.user)}


@router.patch("/complaints/{complaint_id}/status", response_model=dict)
def update_status(complaint_id: str, payload: StatusUpdate, db: DbSession, auth: AuthContext = Depends(require_roles("admin", "officer"))):
    complaint = _accessible_complaint(db, auth, complaint_id)
    _change_status(db, complaint, payload.status, auth.user, payload.note)
    notification_type = "complaint_resolved" if payload.status == "Resolved" else "complaint_in_progress" if payload.status == "In Progress" else "complaint_status"
    title = "Complaint resolved" if payload.status == "Resolved" else "Work started" if payload.status == "In Progress" else "Complaint status updated"
    _notify(db, complaint.citizen_id, complaint.id, title, f"Complaint {complaint.id} moved to {payload.status}", notification_type)
    if auth.user.role == "officer" and payload.status in {"In Progress", "Resolved"}:
        admin_ids = db.scalars(select(User.id).where(User.role == "admin", User.is_active.is_(True))).all()
        for admin_id in admin_ids:
            _notify(db, admin_id, complaint.id, title, f"{auth.user.name} updated complaint {complaint.id} to {payload.status}", notification_type)
    db.commit()
    db.refresh(complaint)
    return {"data": complaint_data(db, complaint, auth.user)}


@router.post("/complaints/{complaint_id}/comments", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_comment(complaint_id: str, payload: CommentCreate, db: DbSession, auth: CurrentAuth):
    complaint = _accessible_complaint(db, auth, complaint_id)
    if payload.is_internal and auth.user.role == "citizen":
        raise HTTPException(status_code=403, detail="Citizens cannot create internal comments")
    comment = ComplaintComment(complaint_id=complaint.id, author_id=auth.user.id, body=payload.body.strip(), is_internal=payload.is_internal)
    db.add(comment)
    if auth.user.id != complaint.citizen_id:
        _notify(db, complaint.citizen_id, complaint.id, "Complaint update", f"A progress update was added to complaint {complaint.id}", "complaint_update")
    db.commit()
    db.refresh(comment)
    return {"data": {"id": comment.id, "author": auth.user.name, "body": comment.body, "is_internal": comment.is_internal, "created_at": comment.created_at}}


@router.post("/complaints/{complaint_id}/attachments", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_attachment(complaint_id: str, db: DbSession, auth: CurrentAuth, file: UploadFile = File(...)):
    complaint = _accessible_complaint(db, auth, complaint_id)
    if auth.user.role == "officer" and complaint.status == "Resolved":
        raise HTTPException(status_code=409, detail="Resolved complaints cannot accept more evidence")
    content = await file.read(settings.max_upload_bytes + 1)
    if not content or len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"Image must be between 1 byte and {settings.max_upload_bytes // (1024 * 1024)} MB")
    detected_type = None
    if content.startswith(b"\xff\xd8\xff"):
        detected_type = "image/jpeg"
    elif content.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_type = "image/png"
    elif len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        detected_type = "image/webp"
    if detected_type is None or file.content_type != detected_type:
        raise HTTPException(status_code=415, detail="Only valid JPEG, PNG, and WebP image files are accepted")
    original_name = Path(file.filename or "image").name[:255]
    suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[detected_type]
    storage_name = f"{uuid4().hex}{suffix}"
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    (settings.upload_dir / storage_name).write_bytes(content)
    attachment = ComplaintAttachment(complaint_id=complaint.id, uploaded_by_id=auth.user.id, storage_name=storage_name, original_name=original_name, content_type=detected_type, size_bytes=len(content))
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return {"data": {"id": attachment.id, "original_name": attachment.original_name, "content_type": attachment.content_type, "size_bytes": attachment.size_bytes, "url": f"/api/attachments/{attachment.id}", "created_at": attachment.created_at}}


@router.get("/attachments/{attachment_id}")
def get_attachment(attachment_id: int, db: DbSession, auth: CurrentAuth):
    attachment = db.get(ComplaintAttachment, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    complaint = db.get(Complaint, attachment.complaint_id)
    if complaint is None or not can_access_complaint(db, auth.user, complaint):
        raise HTTPException(status_code=404, detail="Attachment not found")
    path = settings.upload_dir / attachment.storage_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Attachment file not found")
    return FileResponse(path, media_type=attachment.content_type, filename=attachment.original_name, headers={"X-Content-Type-Options": "nosniff"})
