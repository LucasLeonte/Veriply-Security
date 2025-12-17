"""Sync confidence_logs schema with model (Story 3.4)

Revision ID: 011_sync_confidence_logs_schema
Revises: 010_create_confidence_logs
Create Date: 2025-12-17

Adds missing columns and normalizes types so HITL queries match the ORM
model.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "011_sync_confidence_logs_schema"
down_revision = "010_create_confidence_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add group linkage for RLS-aware analytics
    op.add_column(
        "confidence_logs",
        sa.Column("group_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_confidence_logs_group_id",
        "confidence_logs",
        "groups",
        ["group_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_confidence_logs_group_id",
        "confidence_logs",
        ["group_id"],
    )

    # Align JSON payload field name with ORM (metadata_json)
    op.add_column(
        "confidence_logs",
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )

    # Normalize is_verified_kb to boolean (was varchar)
    op.execute(
        "ALTER TABLE confidence_logs "
        "ALTER COLUMN is_verified_kb TYPE boolean USING (is_verified_kb::boolean)"
    )
    op.execute(
        "ALTER TABLE confidence_logs "
        "ALTER COLUMN is_verified_kb SET DEFAULT false"
    )
    op.execute(
        "ALTER TABLE confidence_logs "
        "ALTER COLUMN is_verified_kb SET NOT NULL"
    )

    # Add open HITL queue index aligned with model
    op.create_index(
        "ix_confidence_logs_hitl_open",
        "confidence_logs",
        ["tenant_id", "group_id", "hitl_resolved"],
    )


def downgrade() -> None:
    op.drop_index("ix_confidence_logs_hitl_open", table_name="confidence_logs")

    op.execute(
        "ALTER TABLE confidence_logs "
        "ALTER COLUMN is_verified_kb TYPE varchar(10) USING "
        "(CASE WHEN is_verified_kb THEN 'true' ELSE 'false' END)"
    )
    op.execute(
        "ALTER TABLE confidence_logs "
        "ALTER COLUMN is_verified_kb SET DEFAULT 'false'"
    )

    op.drop_column("confidence_logs", "metadata_json")

    op.drop_index("ix_confidence_logs_group_id", table_name="confidence_logs")
    op.drop_constraint(
        "fk_confidence_logs_group_id",
        "confidence_logs",
        type_="foreignkey",
    )
    op.drop_column("confidence_logs", "group_id")
