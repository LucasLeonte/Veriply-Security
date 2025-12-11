"""add document status index

Revision ID: 005_add_document_status_index
Revises: 004_create_chunks_table
Create Date: 2025-12-10 12:00:00.000000
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '005_add_document_status_index'
down_revision = '004_create_chunks_table'
branch_labels = None
depends_on = None


def upgrade():
    """Add index on documents.status column for better query performance."""
    op.create_index(
        'ix_documents_status',
        'documents',
        ['status'],
        unique=False
    )


def downgrade():
    """Remove index on documents.status column."""
    op.drop_index('ix_documents_status', table_name='documents')
