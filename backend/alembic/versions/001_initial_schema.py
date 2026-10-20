"""Initial database schema for Muhurta Planner.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-20 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("google_sub", sa.String(length=255), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Asia/Kolkata"),
        sa.Column("default_city", sa.String(length=255), nullable=True),
        sa.Column("telegram_chat_id", sa.String(length=64), nullable=True),
        sa.Column("telegram_link_code", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_unique_constraint("uq_users_google_sub", "users", ["google_sub"])
    op.create_index("ix_users_telegram_link_code", "users", ["telegram_link_code"])

    # ── google_tokens ─────────────────────────────────────────────────────
    op.create_table(
        "google_tokens",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("access_token_enc", sa.Text(), nullable=False),
        sa.Column("refresh_token_enc", sa.Text(), nullable=False),
        sa.Column("expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── plan_requests ─────────────────────────────────────────────────────
    op.create_table(
        "plan_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("parsed_constraints", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=True),
        sa.Column("location_name", sa.String(length=255), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("prompt_variant", sa.String(length=32), nullable=True),
        sa.Column("llm_provider", sa.String(length=32), nullable=True),
        sa.Column("llm_latency_ms", sa.Integer(), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_plan_requests_user_id", "plan_requests", ["user_id"])
    op.create_index("ix_plan_requests_created_at", "plan_requests", ["created_at"])

    # ── slots ─────────────────────────────────────────────────────────────
    op.create_table(
        "slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plan_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("explanation_text", sa.Text(), nullable=True),
        sa.Column("rank", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_slots_plan_request_id", "slots", ["plan_request_id"])

    # ── calendar_events ───────────────────────────────────────────────────
    op.create_table(
        "calendar_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("slots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("google_event_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint("uq_calendar_events_slot_id", "calendar_events", ["slot_id"])
    op.create_index("ix_calendar_events_user_id", "calendar_events", ["user_id"])

    # ── reminders ─────────────────────────────────────────────────────────
    op.create_table(
        "reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("calendar_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("send_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False, server_default="telegram"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reminders_send_at_status", "reminders", ["send_at_utc", "status"])
    op.create_index("ix_reminders_user_id", "reminders", ["user_id"])

    # ── feedback ──────────────────────────────────────────────────────────
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("slots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_feedback_slot_id", "feedback", ["slot_id"])
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"])

    # ── analytics_events ──────────────────────────────────────────────────
    op.create_table(
        "analytics_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plan_requests.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("props", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_analytics_events_name", "analytics_events", ["name"])
    op.create_index("ix_analytics_events_user_id", "analytics_events", ["user_id"])
    op.create_index("ix_analytics_events_plan_request_id", "analytics_events", ["plan_request_id"])


def downgrade() -> None:
    op.drop_table("analytics_events")
    op.drop_table("feedback")
    op.drop_table("reminders")
    op.drop_table("calendar_events")
    op.drop_table("slots")
    op.drop_table("plan_requests")
    op.drop_table("google_tokens")
    op.drop_table("users")
