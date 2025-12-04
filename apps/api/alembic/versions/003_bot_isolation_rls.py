"""Add bot isolation RLS policies to documents, chunks, and embeddings

Revision ID: 003_bot_isolation_rls
Revises: 002_bots_rls
Create Date: 2025-12-04 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_bot_isolation_rls'
down_revision = '002_bots_rls'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable RLS on documents table
    op.execute("ALTER TABLE documents ENABLE ROW LEVEL SECURITY;")
    
    # Policy: Users can only see documents from bots in their tenant
    op.execute("""
        CREATE POLICY documents_bot_isolation ON documents
            FOR ALL
            USING (bot_id IN (
                SELECT id FROM bots 
                WHERE tenant_id = current_setting('app.current_tenant_id')::uuid
            ));
    """)
    
    # Policy: Service role can bypass RLS
    op.execute("""
        CREATE POLICY documents_service_role ON documents
            FOR ALL
            TO service_role
            USING (true);
    """)
    
    # Enable RLS on chunks table
    op.execute("ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;")
    
    # Policy: Users can only access chunks from their bots
    op.execute("""
        CREATE POLICY chunks_bot_isolation ON chunks
            FOR ALL
            USING (bot_id IN (
                SELECT id FROM bots 
                WHERE tenant_id = current_setting('app.current_tenant_id')::uuid
            ));
    """)
    
    # Policy: Service role can bypass RLS
    op.execute("""
        CREATE POLICY chunks_service_role ON chunks
            FOR ALL
            TO service_role
            USING (true);
    """)
    
    # Enable RLS on embeddings table
    op.execute("ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;")
    
    # Policy: Users can only access embeddings from their bots
    op.execute("""
        CREATE POLICY embeddings_bot_isolation ON embeddings
            FOR ALL
            USING (bot_id IN (
                SELECT id FROM bots 
                WHERE tenant_id = current_setting('app.current_tenant_id')::uuid
            ));
    """)
    
    # Policy: Service role can bypass RLS
    op.execute("""
        CREATE POLICY embeddings_service_role ON embeddings
            FOR ALL
            TO service_role
            USING (true);
    """)
    
    # Add CASCADE constraints to ensure data integrity
    op.execute("""
        ALTER TABLE documents 
        DROP CONSTRAINT IF EXISTS fk_documents_bot_id,
        ADD CONSTRAINT fk_documents_bot_id 
            FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE;
    """)
    
    op.execute("""
        ALTER TABLE chunks 
        DROP CONSTRAINT IF EXISTS fk_chunks_bot_id,
        ADD CONSTRAINT fk_chunks_bot_id 
            FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE;
    """)
    
    op.execute("""
        ALTER TABLE embeddings 
        DROP CONSTRAINT IF EXISTS fk_embeddings_bot_id,
        ADD CONSTRAINT fk_embeddings_bot_id 
            FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE;
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS embeddings_service_role ON embeddings;")
    op.execute("DROP POLICY IF EXISTS embeddings_bot_isolation ON embeddings;")
    op.execute("ALTER TABLE embeddings DISABLE ROW LEVEL SECURITY;")
    
    op.execute("DROP POLICY IF EXISTS chunks_service_role ON chunks;")
    op.execute("DROP POLICY IF EXISTS chunks_bot_isolation ON chunks;")
    op.execute("ALTER TABLE chunks DISABLE ROW LEVEL SECURITY;")
    
    op.execute("DROP POLICY IF EXISTS documents_service_role ON documents;")
    op.execute("DROP POLICY IF EXISTS documents_bot_isolation ON documents;")
    op.execute("ALTER TABLE documents DISABLE ROW LEVEL SECURITY;")
