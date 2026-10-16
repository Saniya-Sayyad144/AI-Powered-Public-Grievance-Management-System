from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Complaint, ComplaintAssignment, ComplaintAttachment, ComplaintComment, ComplaintDuplicate, ComplaintStatusHistory, User


def user_data(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "ward": user.ward,
        "role": user.role,
        "department_id": user.department_id,
        "department": user.department.name if user.department else None,
    }


def visible_complaints(db: Session, user: User):
    query = select(Complaint)
    if user.role == "citizen":
        query = query.where(Complaint.citizen_id == user.id)
    elif user.role == "officer":
        query = query.join(ComplaintAssignment).where(
            ComplaintAssignment.officer_id == user.id,
            ComplaintAssignment.is_active.is_(True),
        )
    return query.distinct()


def can_access_complaint(db: Session, user: User, complaint: Complaint) -> bool:
    if user.role == "admin":
        return True
    if user.role == "citizen":
        return complaint.citizen_id == user.id
    return db.scalar(
        select(ComplaintAssignment.id).where(
            ComplaintAssignment.complaint_id == complaint.id,
            ComplaintAssignment.officer_id == user.id,
            ComplaintAssignment.is_active.is_(True),
        )
    ) is not None


def complaint_data(db: Session, complaint: Complaint, viewer: User, detailed: bool = True) -> dict[str, object]:
    active_assignment = db.scalar(
        select(ComplaintAssignment)
        .where(ComplaintAssignment.complaint_id == complaint.id, ComplaintAssignment.is_active.is_(True))
        .order_by(ComplaintAssignment.assigned_at.desc())
    )
    duplicate = db.scalar(
        select(ComplaintDuplicate)
        .where(or_(ComplaintDuplicate.complaint_id == complaint.id, ComplaintDuplicate.possible_duplicate_id == complaint.id))
        .order_by(ComplaintDuplicate.similarity.desc())
    )
    duplicate_label = None
    if duplicate:
        related_id = duplicate.possible_duplicate_id if duplicate.complaint_id == complaint.id else duplicate.complaint_id
        duplicate_label = f"{round(duplicate.similarity * 100)}% similar to {related_id}" if viewer.role == "admin" else f"{round(duplicate.similarity * 100)}% similar to another complaint"

    result: dict[str, object] = {
        "id": complaint.id,
        "title": complaint.title,
        "description": complaint.description,
        "category": complaint.category,
        "status": complaint.status,
        "priority": complaint.priority,
        "location": complaint.location,
        "department": complaint.department.name if complaint.department else "Unassigned",
        "citizen": complaint.citizen.name if viewer.role in {"citizen", "admin"} else "Citizen",
        "officer": active_assignment.officer.name if active_assignment and active_assignment.officer else "Unassigned",
        "date": complaint.created_at,
        "latitude": complaint.latitude,
        "longitude": complaint.longitude,
        "duplicate": duplicate_label,
        "ai_reason": complaint.ai_reason,
        "created_at": complaint.created_at,
        "updated_at": complaint.updated_at,
    }
    if detailed:
        result["history"] = [
            {"previous_status": item.previous_status, "new_status": item.new_status, "note": item.note, "changed_by": item.changed_by.name if viewer.role in {"citizen", "admin"} or item.changed_by.role != "citizen" else "Citizen", "created_at": item.created_at}
            for item in db.scalars(select(ComplaintStatusHistory).where(ComplaintStatusHistory.complaint_id == complaint.id).order_by(ComplaintStatusHistory.created_at))
        ]
        result["comments"] = [
            {"id": item.id, "author": item.author.name if viewer.role == "admin" or item.author_id == viewer.id or item.author.role != "citizen" else "Citizen", "body": item.body, "is_internal": item.is_internal, "created_at": item.created_at}
            for item in db.scalars(select(ComplaintComment).where(ComplaintComment.complaint_id == complaint.id).order_by(ComplaintComment.created_at))
            if not item.is_internal
        ]
        result["attachments"] = [
            {"id": item.id, "original_name": item.original_name, "content_type": item.content_type, "size_bytes": item.size_bytes, "url": f"/api/attachments/{item.id}", "created_at": item.created_at}
            for item in db.scalars(select(ComplaintAttachment).where(ComplaintAttachment.complaint_id == complaint.id).order_by(ComplaintAttachment.created_at))
        ]
        result["assignments"] = [
            {"department": item.department.name, "officer": item.officer.name if item.officer else None, "assigned_by": item.assigned_by.name, "assigned_at": item.assigned_at, "is_active": item.is_active}
            for item in db.scalars(select(ComplaintAssignment).where(ComplaintAssignment.complaint_id == complaint.id).order_by(ComplaintAssignment.assigned_at.desc()))
        ]
    return result
