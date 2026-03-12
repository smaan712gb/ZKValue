"""Add model_usage_records, data_lineage_events, blockchain_anchors, proof_anchor_mappings tables

Revision ID: 003_enterprise_features
Revises: 002_schedules_notifications
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_enterprise_features"
down_revision = "002_schedules_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Enum types (idempotent creation) ---
    op.execute("DO $$ BEGIN CREATE TYPE modelprovider AS ENUM ('deepseek', 'openai', 'anthropic', 'custom'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE lineageeventtype AS ENUM ('data_ingestion', 'preprocessing', 'llm_classification', 'llm_analysis', 'computation', 'proof_generation', 'report_generation', 'anomaly_detection', 'valuation'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE chaintype AS ENUM ('polygon', 'ethereum', 'base'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE anchorstatus AS ENUM ('pending', 'submitted', 'confirmed', 'failed'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # model_usage_records
    op.create_table(
        "model_usage_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("verification_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("verifications.id"), nullable=False),
        sa.Column("provider", postgresql.ENUM("deepseek", "openai", "anthropic", "custom", name="modelprovider", create_type=False), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("response_hash", sa.String(64), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("success", sa.String(10), nullable=False, server_default=sa.text("'true'")),
        sa.Column("error_message", sa.Text(), nullable=True),
    )

    # data_lineage_events
    op.create_table(
        "data_lineage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("verification_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("verifications.id"), nullable=False),
        sa.Column("event_type", postgresql.ENUM(
            "data_ingestion", "preprocessing", "llm_classification", "llm_analysis",
            "computation", "proof_generation", "report_generation", "anomaly_detection", "valuation",
            name="lineageeventtype", create_type=False,
        ), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("output_hash", sa.String(64), nullable=False),
        sa.Column("transformation", sa.String(255), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("parent_event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("data_lineage_events.id"), nullable=True),
    )

    # blockchain_anchors (NOT tenant-scoped)
    op.create_table(
        "blockchain_anchors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("chain", postgresql.ENUM("polygon", "ethereum", "base", name="chaintype", create_type=False), nullable=False),
        sa.Column("merkle_root", sa.String(66), nullable=False),
        sa.Column("proof_count", sa.Integer(), nullable=False),
        sa.Column("tx_hash", sa.String(66), nullable=True),
        sa.Column("block_number", sa.Integer(), nullable=True),
        sa.Column("status", postgresql.ENUM("pending", "submitted", "confirmed", "failed", name="anchorstatus", create_type=False), nullable=False),
        sa.Column("anchor_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("proof_hashes", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("gas_used", sa.Integer(), nullable=True),
        sa.Column("gas_price_gwei", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("contract_address", sa.String(42), nullable=True),
    )

    # proof_anchor_mappings
    op.create_table(
        "proof_anchor_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("anchor_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("verification_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("proof_hash", sa.String(66), nullable=False),
        sa.Column("merkle_index", sa.Integer(), nullable=False),
        sa.Column("merkle_proof", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )

    # Indexes
    op.create_index("ix_model_usage_verification_id", "model_usage_records", ["verification_id"])
    op.create_index("ix_lineage_verification_id", "data_lineage_events", ["verification_id"])
    op.create_index("ix_blockchain_anchors_date", "blockchain_anchors", ["anchor_date"])
    op.create_index("ix_proof_anchor_proof_hash", "proof_anchor_mappings", ["proof_hash"])


def downgrade() -> None:
    op.drop_table("proof_anchor_mappings")
    op.drop_table("blockchain_anchors")
    op.drop_table("data_lineage_events")
    op.drop_table("model_usage_records")
    op.execute("DROP TYPE IF EXISTS modelprovider")
    op.execute("DROP TYPE IF EXISTS lineageeventtype")
    op.execute("DROP TYPE IF EXISTS chaintype")
    op.execute("DROP TYPE IF EXISTS anchorstatus")
