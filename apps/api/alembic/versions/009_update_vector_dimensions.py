"""update vector dimensions from 1024 to 768

Revision ID: 009_update_vector_dimensions
Revises: 008_add_folders_and_bot_access
Create Date: 2025-12-16 16:03:00.000000
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '009_update_vector_dimensions'
down_revision = '008_add_folders_and_bot_access'
branch_labels = None
depends_on = None


def upgrade():
    """Change vector column from 1024 to 768 dimensions to match nomic-embed-text output."""
    conn = op.get_bind()
    
    # Drop existing vector column and recreate with 768 dimensions
    # Note: This will delete existing embeddings, but they can be regenerated
    conn.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS vector;")
    conn.execute("ALTER TABLE chunks ADD COLUMN vector vector(768);")
    
    # Recreate the index if it exists
    conn.execute("DROP INDEX IF EXISTS idx_chunks_tenant_group_vector;")
    conn.execute("""
        CREATE INDEX idx_chunks_tenant_group_vector 
        ON chunks USING ivfflat (vector vector_cosine_ops) 
        WITH (lists = 100)
        WHERE vector IS NOT NULL;
    """)


def downgrade():
    """Revert vector column back to 1024 dimensions."""
    conn = op.get_bind()
    
    # Drop and recreate with 1024 dimensions
    conn.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS vector;")
    conn.execute("ALTER TABLE chunks ADD COLUMN vector vector(1024);")
    
    # Recreate the index
    conn.execute("DROP INDEX IF EXISTS idx_chunks_tenant_group_vector;")
    conn.execute("""
        CREATE INDEX idx_chunks_tenant_group_vector 
        ON chunks USING ivfflat (vector vector_cosine_ops) 
        WITH (lists = 100)
        WHERE vector IS NOT NULL;
    """)
