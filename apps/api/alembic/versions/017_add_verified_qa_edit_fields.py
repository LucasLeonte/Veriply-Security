"""Add soft delete and edit tracking to verified_qa table.

Revision ID: 017
Revises: 016
Create Date: 2026-01-08

This migration adds:
- deleted_at: Soft delete timestamp (NULL if active)
- updated_by_user_id: Track which user last edited the entry
- Indexes for efficient filtering and auditing
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '017_add_verified_qa_edit_fields'
down_revision = '016_update_email_integrations_monitoring'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to verified_qa table
    op.add_column(
        'verified_qa',
        sa.Column(
            'updated_by_user_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='User ID of the last user to edit this entry'
        )
    )
    
    op.add_column(
        'verified_qa',
        sa.Column(
            'deleted_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Soft delete timestamp; NULL if entry is active'
        )
    )
    
    # Add foreign key constraint for updated_by_user_id
    op.create_foreign_key(
        'fk_verified_qa_updated_by_user_id',
        'verified_qa',
        'users',
        ['updated_by_user_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Add indexes for efficient filtering
    op.create_index(
        'idx_verified_qa_updated_by',
        'verified_qa',
        ['updated_by_user_id'],
    )
    
    op.create_index(
        'idx_verified_qa_deleted_at',
        'verified_qa',
        ['deleted_at'],
    )
    
    # Index for filtering out soft-deleted entries efficiently
    op.create_index(
        'idx_verified_qa_active',
        'verified_qa',
        ['deleted_at', 'group_id'],
        postgresql_where=sa.text('deleted_at IS NULL'),
    )


def downgrade():
    # Remove indexes
    op.drop_index('idx_verified_qa_active', table_name='verified_qa')
    op.drop_index('idx_verified_qa_deleted_at', table_name='verified_qa')
    op.drop_index('idx_verified_qa_updated_by', table_name='verified_qa')
    
    # Remove foreign key
    op.drop_constraint('fk_verified_qa_updated_by_user_id', 'verified_qa', type_='foreignkey')
    
    # Remove columns
    op.drop_column('verified_qa', 'deleted_at')
    op.drop_column('verified_qa', 'updated_by_user_id')
