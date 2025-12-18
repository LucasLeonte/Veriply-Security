"""add pgvector HNSW index for semantic search

Revision ID: 005_add_hnsw_index
Revises: 004_create_chunks_table
Create Date: 2025-12-11 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_add_hnsw_index'
down_revision = '004_create_chunks_table'
branch_labels = None
depends_on = None


def upgrade():
    """Add HNSW index for fast vector search and composite index for RLS filtering."""
    conn = op.get_bind()

    # Create HNSW index for fast approximate nearest neighbor search
    # Using cosine distance (vector_cosine_ops) for semantic similarity
    # Parameters:
    #   m = 16: max number of connections per layer (recall/speed tradeoff)
    #   ef_construction = 64: size of dynamic candidate list during construction
    # These parameters provide ~15% recall loss for 2x speed improvement
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
        ON chunks 
        USING hnsw (vector vector_cosine_ops) 
        WITH (m = 16, ef_construction = 64);
    """)

    # Create composite index on (bot_id, tenant_id) for efficient RLS filtering
    # This speeds up queries that filter by both bot and tenant before vector search
    op.create_index(
        'idx_chunks_bot_tenant',
        'chunks',
        ['bot_id', 'tenant_id'],
        unique=False
    )

    # Add page_number column for section/page reference in search results
    op.add_column('chunks', sa.Column('page_number', sa.Integer, nullable=True))

    # Add updated_at column for tracking modifications
    op.add_column(
        'chunks',
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text('now()'),
            onupdate=sa.text('now()'),
            nullable=True
        )
    )


def downgrade():
    """Remove HNSW index and composite indexes."""
    conn = op.get_bind()

    # Drop HNSW index
    conn.execute("DROP INDEX IF EXISTS idx_chunks_embedding_hnsw;")

    # Drop composite index
    op.drop_index('idx_chunks_bot_tenant', table_name='chunks')

    # Drop added columns
    op.drop_column('chunks', 'page_number')
    op.drop_column('chunks', 'updated_at')
