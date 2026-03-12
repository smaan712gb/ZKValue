"""Initial migration - create all base tables

Revision ID: 001_initial
Revises:
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Enum types (idempotent creation) ---
    op.execute("DO $$ BEGIN CREATE TYPE orgplan AS ENUM ('starter', 'professional', 'enterprise'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE userrole AS ENUM ('owner', 'admin', 'analyst', 'viewer'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE verificationmodule AS ENUM ('private_credit', 'ai_ip_valuation'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE verificationstatus AS ENUM ('pending', 'processing', 'completed', 'failed'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE assettype AS ENUM ('training_data', 'model_weights', 'inference_infra', 'deployed_app'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE valuationmethod AS ENUM ('cost_approach', 'market_approach', 'income_approach'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # --- organizations ---
    op.create_table(
        "organizations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column(
            "plan",
            postgresql.ENUM("starter", "professional", "enterprise", name="orgplan", create_type=False),
            nullable=False,
            server_default="starter",
        ),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("settings", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("llm_provider", sa.String(50), nullable=False, server_default="deepseek"),
        sa.Column("llm_model", sa.String(100), nullable=False, server_default="deepseek-chat"),
        sa.Column("max_verifications_per_month", sa.Integer(), nullable=False, server_default=sa.text("10")),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    # --- users ---
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column(
            "role",
            postgresql.ENUM("owner", "admin", "analyst", "viewer", name="userrole", create_type=False),
            nullable=False,
            server_default="analyst",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_organization_id", "users", ["organization_id"], unique=False)

    # --- verifications ---
    op.create_table(
        "verifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "module",
            postgresql.ENUM("private_credit", "ai_ip_valuation", name="verificationmodule", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "processing", "completed", "failed", name="verificationstatus", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("input_data", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("result_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("proof_hash", sa.String(255), nullable=True),
        sa.Column("proof_certificate_url", sa.Text(), nullable=True),
        sa.Column("report_url", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_verifications_organization_id", "verifications", ["organization_id"], unique=False)
    op.create_index("ix_verifications_module", "verifications", ["module"], unique=False)
    op.create_index("ix_verifications_status", "verifications", ["status"], unique=False)

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("details", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"], unique=False)
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)

    # --- credit_portfolios ---
    op.create_table(
        "credit_portfolios",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "verification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("verifications.id"),
            nullable=False,
        ),
        sa.Column("portfolio_name", sa.String(255), nullable=False),
        sa.Column("fund_name", sa.String(255), nullable=False),
        sa.Column("loan_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_principal", sa.Numeric(precision=18, scale=2), nullable=False, server_default=sa.text("0.0")),
        sa.Column("weighted_avg_rate", sa.Numeric(precision=10, scale=6), nullable=False, server_default=sa.text("0.0")),
        sa.Column("avg_ltv_ratio", sa.Numeric(precision=10, scale=6), nullable=False, server_default=sa.text("0.0")),
        sa.Column("nav_value", sa.Numeric(precision=18, scale=2), nullable=False, server_default=sa.text("0.0")),
        sa.Column("covenant_compliance_status", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("loan_tape_url", sa.Text(), nullable=True),
    )
    op.create_index("ix_credit_portfolios_organization_id", "credit_portfolios", ["organization_id"], unique=False)

    # --- ai_assets ---
    op.create_table(
        "ai_assets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "verification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("verifications.id"),
            nullable=False,
        ),
        sa.Column(
            "asset_type",
            postgresql.ENUM("training_data", "model_weights", "inference_infra", "deployed_app", name="assettype", create_type=False),
            nullable=False,
        ),
        sa.Column("asset_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "valuation_method",
            postgresql.ENUM("cost_approach", "market_approach", "income_approach", name="valuationmethod", create_type=False),
            nullable=False,
        ),
        sa.Column("estimated_value", sa.Numeric(precision=18, scale=2), nullable=False, server_default=sa.text("0.0")),
        sa.Column("confidence_score", sa.Numeric(precision=5, scale=4), nullable=False, server_default=sa.text("0.0")),
        sa.Column("valuation_inputs", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("valuation_breakdown", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("ias38_compliant", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("asc350_compliant", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_ai_assets_organization_id", "ai_assets", ["organization_id"], unique=False)
    op.create_index("ix_ai_assets_asset_type", "ai_assets", ["asset_type"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_index("ix_ai_assets_asset_type", table_name="ai_assets")
    op.drop_index("ix_ai_assets_organization_id", table_name="ai_assets")
    op.drop_table("ai_assets")

    op.drop_index("ix_credit_portfolios_organization_id", table_name="credit_portfolios")
    op.drop_table("credit_portfolios")

    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_organization_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_verifications_status", table_name="verifications")
    op.drop_index("ix_verifications_module", table_name="verifications")
    op.drop_index("ix_verifications_organization_id", table_name="verifications")
    op.drop_table("verifications")

    op.drop_index("ix_users_organization_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS valuationmethod")
    op.execute("DROP TYPE IF EXISTS assettype")
    op.execute("DROP TYPE IF EXISTS verificationstatus")
    op.execute("DROP TYPE IF EXISTS verificationmodule")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS orgplan")
