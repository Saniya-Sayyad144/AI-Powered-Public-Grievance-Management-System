from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('citizen', 'admin', 'officer')", name="ck_users_role"),
        Index("ix_users_role_department", "role", "department_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    ward: Mapped[str | None] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="citizen")
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    department: Mapped["Department | None"] = relationship(back_populates="users")
    complaints: Mapped[list["Complaint"]] = relationship(back_populates="citizen", foreign_keys="Complaint.citizen_id")


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="department")
    complaints: Mapped[list["Complaint"]] = relationship(back_populates="department")


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (
        CheckConstraint("status IN ('Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved')", name="ck_complaints_status"),
        CheckConstraint("priority IN ('Low', 'Medium', 'High', 'Critical')", name="ck_complaints_priority"),
        Index("ix_complaints_status_category_created", "status", "category", "created_at"),
        Index("ix_complaints_citizen_created", "citizen_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    citizen_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="Submitted")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="Medium")
    location: Mapped[str] = mapped_column(String(240), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), index=True)
    ai_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    citizen: Mapped[User] = relationship(back_populates="complaints", foreign_keys=[citizen_id])
    department: Mapped[Department | None] = relationship(back_populates="complaints")
    assignments: Mapped[list["ComplaintAssignment"]] = relationship(back_populates="complaint", cascade="all, delete-orphan")
    status_history: Mapped[list["ComplaintStatusHistory"]] = relationship(back_populates="complaint", cascade="all, delete-orphan", order_by="ComplaintStatusHistory.created_at")
    comments: Mapped[list["ComplaintComment"]] = relationship(back_populates="complaint", cascade="all, delete-orphan")
    attachments: Mapped[list["ComplaintAttachment"]] = relationship(back_populates="complaint", cascade="all, delete-orphan")


class ComplaintAssignment(Base):
    __tablename__ = "complaint_assignments"
    __table_args__ = (Index("ix_assignments_officer_active", "officer_id", "is_active"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    officer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    assigned_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    complaint: Mapped[Complaint] = relationship(back_populates="assignments")
    department: Mapped[Department] = relationship()
    officer: Mapped[User | None] = relationship(foreign_keys=[officer_id])
    assigned_by: Mapped[User] = relationship(foreign_keys=[assigned_by_id])


class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"
    __table_args__ = (Index("ix_status_history_complaint_created", "complaint_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(24))
    new_status: Mapped[str] = mapped_column(String(24), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500))
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    complaint: Mapped[Complaint] = relationship(back_populates="status_history")
    changed_by: Mapped[User] = relationship()


class ComplaintComment(Base):
    __tablename__ = "complaint_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    complaint: Mapped[Complaint] = relationship(back_populates="comments")
    author: Mapped[User] = relationship()


class ComplaintDuplicate(Base):
    __tablename__ = "complaint_duplicates"
    __table_args__ = (
        UniqueConstraint("complaint_id", "possible_duplicate_id", name="uq_complaint_duplicate_pair"),
        CheckConstraint("complaint_id <> possible_duplicate_id", name="ck_complaint_duplicate_not_self"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    possible_duplicate_id: Mapped[str] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    similarity: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_read_created", "user_id", "is_read", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    complaint_id: Mapped[str | None] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(120), nullable=False, default="CivicPulse update", server_default="CivicPulse update")
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(40), nullable=False, default="update", server_default="update")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped[User] = relationship()
    complaint: Mapped[Complaint | None] = relationship()


class CitizenFeedback(Base):
    __tablename__ = "citizen_feedback"
    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="ck_feedback_rating"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    citizen_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    complaint_id: Mapped[str | None] = mapped_column(ForeignKey("complaints.id", ondelete="SET NULL"), index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comments: Mapped[str | None] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    citizen: Mapped[User] = relationship()
    complaint: Mapped[Complaint | None] = relationship()


class ComplaintAttachment(Base):
    __tablename__ = "complaint_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    storage_name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    complaint: Mapped[Complaint] = relationship(back_populates="attachments")
    uploaded_by: Mapped[User] = relationship()


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class UserInvitation(Base):
    __tablename__ = "user_invitations"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'officer')", name="ck_user_invitations_role"),
        Index("ix_user_invitations_code_hash", "code_hash", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"))
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
