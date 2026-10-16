"""Add notification titles and event types.

Revision ID: 20261016_0003
Revises: 20261016_0002
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa

revision = "20261016_0003"
down_revision = "20261016_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column("title", sa.String(length=120), server_default="CivicPulse update", nullable=False),
    )
    op.add_column(
        "notifications",
        sa.Column("notification_type", sa.String(length=40), server_default="update", nullable=False),
    )
    op.alter_column("notifications", "title", server_default=None)
    op.alter_column("notifications", "notification_type", server_default=None)


def downgrade() -> None:
    op.drop_column("notifications", "notification_type")
    op.drop_column("notifications", "title")