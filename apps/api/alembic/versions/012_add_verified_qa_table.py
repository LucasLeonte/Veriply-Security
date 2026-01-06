"""Add verified_qa table for storing human-approved Q&A pairs

Revision ID: 012_add_verified_qa_table
Revises: 011_update_confidence_logs
Create Date: 2026-01-06

This migration creates the verified_qa table to store human-validated Q&A pairs
from HITL approvals, enabling the Trust Loop feature where verified answers
take precedence over RAG-generated responses.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "012_add_verified_qa_table"
down_revision = ("011_add_chat_messages_log", "011_update_confidence_logs")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create verified_qa table with vector embeddings and RLS policies."""
    conn = op.get_bind()
    
    # Ensure pgvector extension is available
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector;"))
    
    # Create verified_qa table
    op.create_table(
        "verified_qa",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("source_citations", postgresql.JSONB(), nullable=True),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    
    # Add question_text length constraint
    op.create_check_constraint(
        "ck_verified_qa_question_length",
        "verified_qa",
        "length(question_text) <= 2000"
    )
    
    # Add vector column for question embeddings (768 dimensions for nomic-embed-text)
    conn.execute(sa.text("ALTER TABLE verified_qa ADD COLUMN question_embedding vector(768);"))
    
    # Create vector index for fast semantic search using IVFFlat
    # lists=100 is optimal for datasets <10K vectors
    conn.execute(sa.text("""
        CREATE INDEX idx_verified_qa_embedding 
        ON verified_qa 
        USING ivfflat (question_embedding vector_cosine_ops)
        WITH (lists = 100)
        WHERE question_embedding IS NOT NULL;
    """))
    
    # Create composite indexes for scoped queries
    op.create_index(
        "idx_verified_qa_scope",
        "verified_qa",
        ["tenant_id", "group_id", "bot_id"],
        unique=False
    )
    
    op.create_index(
        "idx_verified_qa_tenant_group",
        "verified_qa",
        ["tenant_id", "group_id"],
        unique=False
    )
    
    # Create indexes for foreign keys
    op.create_index("idx_verified_qa_tenant_id", "verified_qa", ["tenant_id"], unique=False)
    op.create_index("idx_verified_qa_group_id", "verified_qa", ["group_id"], unique=False)
    op.create_index("idx_verified_qa_bot_id", "verified_qa", ["bot_id"], unique=False)
    op.create_index("idx_verified_qa_approved_by", "verified_qa", ["approved_by_user_id"], unique=False)
    op.create_index("idx_verified_qa_approved_at", "verified_qa", ["approved_at"], unique=False)
    
    # Enable Row Level Security
    conn.execute(sa.text("ALTER TABLE verified_qa ENABLE ROW LEVEL SECURITY;"))
    
    # Create RLS policy for tenant + group isolation
    conn.execute(sa.text("""
        CREATE POLICY verified_qa_isolation ON verified_qa
        FOR ALL
        USING (
            tenant_id = current_setting('app.current_tenant_id', true)::uuid 
            AND group_id = current_setting('app.current_group_id', true)::uuid
        );
    """))
    
    # Create service role bypass policy for background jobs
    conn.execute(sa.text("""
        CREATE POLICY verified_qa_service_role ON verified_qa
        FOR ALL
        TO service_role
        USING (true);
    """))


def downgrade() -> None:
    """Drop verified_qa table and all associated objects."""
    conn = op.get_bind()
    
    # Drop RLS policies
    conn.execute(sa.text("DROP POLICY IF EXISTS verified_qa_service_role ON verified_qa;"))
    conn.execute(sa.text("DROP POLICY IF EXISTS verified_qa_isolation ON verified_qa;"))
    
    # Disable RLS
    conn.execute(sa.text("ALTER TABLE verified_qa DISABLE ROW LEVEL SECURITY;"))
    
    # Drop indexes (will cascade with table, but explicit for clarity)
    op.drop_index("idx_verified_qa_approved_at", table_name="verified_qa")
    op.drop_index("idx_verified_qa_approved_by", table_name="verified_qa")
    op.drop_index("idx_verified_qa_bot_id", table_name="verified_qa")
    op.drop_index("idx_verified_qa_group_id", table_name="verified_qa")
    op.drop_index("idx_verified_qa_tenant_id", table_name="verified_qa")
    op.drop_index("idx_verified_qa_tenant_group", table_name="verified_qa")
    op.drop_index("idx_verified_qa_scope", table_name="verified_qa")
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_verified_qa_embedding;"))
    
    # Drop table (cascades to constraints and remaining indexes)
    op.drop_table("verified_qa")
