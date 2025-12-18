"""create chunks table

Revision ID: 004_create_chunks_table
Revises: 003_bot_isolation_rls
Create Date: 2025-12-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = '004_create_chunks_table'
down_revision = '003_bot_isolation_rls'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # ensure pgvector extension exists
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.create_table(
        'chunks',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('document_id', pg.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('tenant_id', pg.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('bot_id', pg.UUID(as_uuid=True), sa.ForeignKey('bots.id'), nullable=True),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('metadata', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('ix_chunks_document_id', 'chunks', ['document_id'])
    op.create_index('ix_chunks_tenant_id', 'chunks', ['tenant_id'])
    op.create_index('ix_chunks_bot_id', 'chunks', ['bot_id'])

    # add pgvector column now that extension is present
    conn.execute("ALTER TABLE chunks ADD COLUMN vector vector;")

    # ensure uniqueness for idempotency
    op.create_unique_constraint('uq_chunks_document_chunk', 'chunks', ['document_id', 'chunk_index'])


def downgrade():
    op.drop_constraint('uq_chunks_document_chunk', 'chunks', type_='unique')
    op.drop_index('ix_chunks_bot_id', table_name='chunks')
    op.drop_index('ix_chunks_tenant_id', table_name='chunks')
    op.drop_index('ix_chunks_document_id', table_name='chunks')
    op.drop_table('chunks')