"""Update confidence_logs schema for HITL and audit fields

Revision ID: 011_update_confidence_logs
Revises: 011_sync_confidence_logs_schema
Create Date: 2025-12-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "011_update_confidence_logs"
down_revision = "011_sync_confidence_logs_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert is_verified_kb from string to boolean
    op.alter_column(
        "confidence_logs",
        "is_verified_kb",
        existing_type=sa.String(length=10),
        type_=sa.Boolean(),
        server_default=sa.text("false"),
        postgresql_using="is_verified_kb::boolean",
        nullable=False,
    )

    # Add new columns
    op.add_column("confidence_logs", sa.Column("group_id", sa.Uuid(), nullable=True))
    op.add_column("confidence_logs", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.add_column(
        "confidence_logs",
        sa.Column("hitl_resolved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("confidence_logs", sa.Column("resolution_user_id", sa.Uuid(), nullable=True))
    op.add_column("confidence_logs", sa.Column("resolution_timestamp", sa.DateTime(), nullable=True))
    op.add_column("confidence_logs", sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Foreign keys
    op.create_foreign_key(
        "fk_conf_logs_group_id",
        "confidence_logs",
        "groups",
        ["group_id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_conf_logs_user_id",
        "confidence_logs",
        "users",
        ["user_id"],
    )
    op.create_foreign_key(
        "fk_conf_logs_resolution_user_id",
        "confidence_logs",
        "users",
        ["resolution_user_id"],
    )

    # Indexes
    op.create_index("ix_confidence_logs_group_id", "confidence_logs", ["group_id"])
    op.create_index(
        "ix_confidence_logs_hitl_open",
        "confidence_logs",
        ["tenant_id", "group_id", "hitl_resolved"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_confidence_logs_hitl_open", table_name="confidence_logs")
    op.drop_index("ix_confidence_logs_group_id", table_name="confidence_logs")

    # Drop foreign keys
    op.drop_constraint("fk_conf_logs_resolution_user_id", "confidence_logs", type_="foreignkey")
    op.drop_constraint("fk_conf_logs_user_id", "confidence_logs", type_="foreignkey")
    op.drop_constraint("fk_conf_logs_group_id", "confidence_logs", type_="foreignkey")

    # Drop added columns
    op.drop_column("confidence_logs", "metadata_json")
    op.drop_column("confidence_logs", "resolution_timestamp")
    op.drop_column("confidence_logs", "resolution_user_id")
    op.drop_column("confidence_logs", "hitl_resolved")
    op.drop_column("confidence_logs", "user_id")
    op.drop_column("confidence_logs", "group_id")

    # Convert is_verified_kb back to string
    op.alter_column(
        "confidence_logs",
        "is_verified_kb",
        existing_type=sa.Boolean(),
        type_=sa.String(length=10),
        server_default="false",
        postgresql_using="CASE WHEN is_verified_kb THEN 'true' ELSE 'false' END",
        nullable=False,
    )
