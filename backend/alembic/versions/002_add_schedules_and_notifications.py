"""Add verification_schedules, drift_alerts, notifications, notification_preferences tables

Revision ID: 002_schedules_notifications
Revises: 001_initial
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_schedules_notifications"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Enum types (idempotent creation) ---
    op.execute("DO $$ BEGIN CREATE TYPE schedulefrequency AS ENUM ('daily', 'weekly', 'monthly', 'quarterly'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE alertseverity AS ENUM ('info', 'warning', 'critical'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE alertstatus AS ENUM ('active', 'acknowledged', 'resolved'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE notificationtype AS ENUM ('verification_completed', 'verification_failed', 'drift_alert', 'covenant_breach', 'usage_limit_warning', 'schedule_executed'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE notificationchannel AS ENUM ('in_app', 'email', 'webhook', 'slack'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # verification_schedules
    op.create_table(
        "verification_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("module", sa.String(50), nullable=False),
        sa.Column("frequency", postgresql.ENUM("daily", "weekly", "monthly", "quarterly", name="schedulefrequency", create_type=False), nullable=False),
        sa.Column("input_data", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("drift_threshold_pct", sa.Numeric(5, 2), nullable=False, server_default=sa.text("10.0")),
        sa.Column("last_verification_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("verifications.id"), nullable=True),
        sa.Column("run_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )

    # drift_alerts
    op.create_table(
        "drift_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("schedule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("verification_schedules.id"), nullable=False),
        sa.Column("verification_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("verifications.id"), nullable=False),
        sa.Column("previous_verification_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("verifications.id"), nullable=True),
        sa.Column("severity", postgresql.ENUM("info", "warning", "critical", name="alertseverity", create_type=False), nullable=False),
        sa.Column("status", postgresql.ENUM("active", "acknowledged", "resolved", name="alertstatus", create_type=False), nullable=False, server_default=sa.text("'active'")),
        sa.Column("alert_type", sa.String(100), nullable=False),
        sa.Column("message", sa.String(1000), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("drift_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("acknowledged_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )

    # notifications
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notification_type", postgresql.ENUM(
            "verification_completed", "verification_failed", "drift_alert",
            "covenant_breach", "usage_limit_warning", "schedule_executed",
            name="notificationtype", create_type=False,
        ), nullable=False),
        sa.Column("channel", postgresql.ENUM("in_app", "email", "webhook", "slack", name="notificationchannel", create_type=False), nullable=False, server_default=sa.text("'in_app'")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reference_id", sa.String(255), nullable=True),
        sa.Column("reference_type", sa.String(50), nullable=True),
    )

    # notification_preferences
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("notification_type", postgresql.ENUM(
            "verification_completed", "verification_failed", "drift_alert",
            "covenant_breach", "usage_limit_warning", "schedule_executed",
            name="notificationtype", create_type=False,
        ), nullable=False),
        sa.Column("channel", postgresql.ENUM("in_app", "email", "webhook", "slack", name="notificationchannel", create_type=False), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("webhook_url", sa.String(1000), nullable=True),
        sa.Column("slack_webhook_url", sa.String(1000), nullable=True),
        sa.Column("email_address", sa.String(255), nullable=True),
    )

    # Indexes for common queries
    op.create_index("ix_drift_alerts_schedule_id", "drift_alerts", ["schedule_id"])
    op.create_index("ix_drift_alerts_status", "drift_alerts", ["status"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notification_preferences_user_id", "notification_preferences", ["user_id"])


def downgrade() -> None:
    op.drop_table("notification_preferences")
    op.drop_table("notifications")
    op.drop_table("drift_alerts")
    op.drop_table("verification_schedules")
    op.execute("DROP TYPE IF EXISTS schedulefrequency")
    op.execute("DROP TYPE IF EXISTS alertseverity")
    op.execute("DROP TYPE IF EXISTS alertstatus")
    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS notificationchannel")
