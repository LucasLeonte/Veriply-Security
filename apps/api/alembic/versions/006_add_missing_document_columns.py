"""add missing document columns

Revision ID: 006_add_missing_document_columns
Revises: 005_add_hnsw_index
Create Date: 2025-12-16 11:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '006_add_missing_document_columns'
down_revision = '005_add_hnsw_index'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to documents table if they don't exist
    # Note: Using title column (which already exists) instead of filename
    
    # Add mime column
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='documents' AND column_name='mime') THEN
                ALTER TABLE documents ADD COLUMN mime VARCHAR(100);
            END IF;
        END $$;
    """)
    
    # Add size column
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='documents' AND column_name='size') THEN
                ALTER TABLE documents ADD COLUMN size INTEGER;
            END IF;
        END $$;
    """)
    
    # Add storage_path column
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='documents' AND column_name='storage_path') THEN
                ALTER TABLE documents ADD COLUMN storage_path TEXT;
            END IF;
        END $$;
    """)
    
    # Add uploaded_by column
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='documents' AND column_name='uploaded_by') THEN
                ALTER TABLE documents ADD COLUMN uploaded_by UUID REFERENCES users(id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Remove added columns
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS uploaded_by;")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS storage_path;")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS size;")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS mime;")
