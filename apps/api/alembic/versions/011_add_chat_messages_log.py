"""add chat message log table

Revision ID: 011_add_chat_messages_log
Revises: 010_add_bot_public_fields
Create Date: 2025-12-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "011_add_chat_messages_log"
down_revision = "010_add_bot_public_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("bot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bots.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("client_message_id", sa.String(length=255), nullable=True),
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_index(
        "ix_chat_messages_bot_created",
        "chat_messages",
        ["bot_id", "created_at"],
    )
    op.create_index(
        "ix_chat_messages_bot_session",
        "chat_messages",
        ["bot_id", "session_id", "created_at"],
    )
    op.create_index(
        "ix_chat_messages_bot_answer",
        "chat_messages",
        ["bot_id", "answer_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_chat_messages_bot_answer", table_name="chat_messages")
    op.drop_index("ix_chat_messages_bot_session", table_name="chat_messages")
    op.drop_index("ix_chat_messages_bot_created", table_name="chat_messages")
    op.drop_table("chat_messages")
