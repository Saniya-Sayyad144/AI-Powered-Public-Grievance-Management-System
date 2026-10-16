"""Initial CivicPulse schema.

Revision ID: 20261014_0001
Revises:
Create Date: 2026-10-14
"""
from alembic import op
import sqlalchemy as sa

revision = "20261014_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("ward", sa.String(length=80), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('citizen', 'admin', 'officer')", name="ck_users_role"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_department_id", "users", ["department_id"])
    op.create_index("ix_users_role_department", "users", ["role", "department_id"])

    op.create_table(
        "complaints",
        sa.Column("id", sa.String(length=24), nullable=False),
        sa.Column("citizen_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("location", sa.String(length=240), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("ai_reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved')", name="ck_complaints_status"),
        sa.CheckConstraint("priority IN ('Low', 'Medium', 'High', 'Critical')", name="ck_complaints_priority"),
        sa.ForeignKeyConstraint(["citizen_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_complaints_created_at", "complaints", ["created_at"])
    op.create_index("ix_complaints_department_id", "complaints", ["department_id"])
    op.create_index("ix_complaints_status_category_created", "complaints", ["status", "category", "created_at"])
    op.create_index("ix_complaints_citizen_created", "complaints", ["citizen_id", "created_at"])

    op.create_table(
        "complaint_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("complaint_id", sa.String(length=24), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("officer_id", sa.Integer(), nullable=True),
        sa.Column("assigned_by_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["officer_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_complaint_assignments_complaint_id", "complaint_assignments", ["complaint_id"])
    op.create_index("ix_complaint_assignments_officer_id", "complaint_assignments", ["officer_id"])
    op.create_index("ix_assignments_officer_active", "complaint_assignments", ["officer_id", "is_active"])

    op.create_table(
        "complaint_status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("complaint_id", sa.String(length=24), nullable=False),
        sa.Column("previous_status", sa.String(length=24), nullable=True),
        sa.Column("new_status", sa.String(length=24), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("changed_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_status_history_complaint_created", "complaint_status_history", ["complaint_id", "created_at"])

    op.create_table(
        "complaint_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("complaint_id", sa.String(length=24), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_complaint_comments_complaint_id", "complaint_comments", ["complaint_id"])

    op.create_table(
        "complaint_duplicates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("complaint_id", sa.String(length=24), nullable=False),
        sa.Column("possible_duplicate_id", sa.String(length=24), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("complaint_id <> possible_duplicate_id", name="ck_complaint_duplicate_not_self"),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["possible_duplicate_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complaint_id", "possible_duplicate_id", name="uq_complaint_duplicate_pair"),
    )
    op.create_index("ix_complaint_duplicates_complaint_id", "complaint_duplicates", ["complaint_id"])
    op.create_index("ix_complaint_duplicates_possible_duplicate_id", "complaint_duplicates", ["possible_duplicate_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("complaint_id", sa.String(length=24), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_read_created", "notifications", ["user_id", "is_read", "created_at"])

    op.create_table(
        "citizen_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("citizen_id", sa.Integer(), nullable=False),
        sa.Column("complaint_id", sa.String(length=24), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comments", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_feedback_rating"),
        sa.ForeignKeyConstraint(["citizen_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_citizen_feedback_citizen_id", "citizen_feedback", ["citizen_id"])
    op.create_index("ix_citizen_feedback_complaint_id", "citizen_feedback", ["complaint_id"])

    op.create_table(
        "complaint_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("complaint_id", sa.String(length=24), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=False),
        sa.Column("storage_name", sa.String(length=120), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_name"),
    )
    op.create_index("ix_complaint_attachments_complaint_id", "complaint_attachments", ["complaint_id"])

    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("jti"),
    )
    op.create_index("ix_revoked_tokens_expires_at", "revoked_tokens", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_revoked_tokens_expires_at", table_name="revoked_tokens")
    op.drop_table("revoked_tokens")
    op.drop_index("ix_complaint_attachments_complaint_id", table_name="complaint_attachments")
    op.drop_table("complaint_attachments")
    op.drop_index("ix_citizen_feedback_complaint_id", table_name="citizen_feedback")
    op.drop_index("ix_citizen_feedback_citizen_id", table_name="citizen_feedback")
    op.drop_table("citizen_feedback")
    op.drop_index("ix_notifications_user_read_created", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_complaint_duplicates_possible_duplicate_id", table_name="complaint_duplicates")
    op.drop_index("ix_complaint_duplicates_complaint_id", table_name="complaint_duplicates")
    op.drop_table("complaint_duplicates")
    op.drop_index("ix_complaint_comments_complaint_id", table_name="complaint_comments")
    op.drop_table("complaint_comments")
    op.drop_index("ix_status_history_complaint_created", table_name="complaint_status_history")
    op.drop_table("complaint_status_history")
    op.drop_table("complaint_assignments")
    op.drop_index("ix_complaints_citizen_created", table_name="complaints")
    op.drop_index("ix_complaints_status_category_created", table_name="complaints")
    op.drop_index("ix_complaints_department_id", table_name="complaints")
    op.drop_index("ix_complaints_created_at", table_name="complaints")
    op.drop_table("complaints")
    op.drop_index("ix_users_role_department", table_name="users")
    op.drop_index("ix_users_department_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("departments")
