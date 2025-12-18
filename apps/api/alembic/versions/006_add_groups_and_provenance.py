"""Add groups, group_members, and update bot/document/chunk models for group scoping and provenance.

Revision ID: 006_add_groups_and_provenance
Revises: 006_add_missing_document_columns
Create Date: 2025-12-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_add_groups_and_provenance'
down_revision = '006_add_missing_document_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create groups table
    op.create_table(
        'groups',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_groups_tenant_name'),
    )
    op.create_index('ix_groups_tenant_id', 'groups', ['tenant_id'], unique=False)
    op.create_index('ix_groups_tenant_name', 'groups', ['tenant_id', 'name'], unique=False)

    # Create group_members table
    op.create_table(
        'group_members',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('group_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.Enum('group_admin', 'manager', 'operator', name='grouprole'), nullable=False),
        sa.Column('invited_at', sa.DateTime(), nullable=False),
        sa.Column('invited_by_id', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'user_id', name='uq_group_members_group_user'),
    )
    op.create_index('ix_group_members_group_id', 'group_members', ['group_id'], unique=False)
    op.create_index('ix_group_members_group_user', 'group_members', ['group_id', 'user_id'], unique=False)
    op.create_index('ix_group_members_user_id', 'group_members', ['user_id'], unique=False)

    # Add group_id to bots table
    op.add_column('bots', sa.Column('group_id', sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")))
    op.create_foreign_key('fk_bots_group_id', 'bots', 'groups', ['group_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_bots_group_id', 'bots', ['group_id'], unique=False)
    op.create_index('ix_bots_tenant_group', 'bots', ['tenant_id', 'group_id'], unique=False)
    
    # Update bot unique constraint
    op.drop_constraint('uq_bots_tenant_name', 'bots', type_='unique')
    op.create_unique_constraint('uq_bots_tenant_group_name', 'bots', ['tenant_id', 'group_id', 'name'])

    # Add group_id and columns to documents table
    op.add_column('documents', sa.Column('group_id', sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")))
    op.add_column('documents', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.alter_column('documents', 'uploaded_by', new_column_name='uploader_id', existing_type=sa.Uuid(), nullable=False)
    
    op.create_foreign_key('fk_documents_group_id', 'documents', 'groups', ['group_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_documents_deleted', 'documents', ['deleted_at'], unique=False)
    op.create_index('ix_documents_group_id', 'documents', ['group_id'], unique=False)
    op.create_index('ix_documents_tenant_group', 'documents', ['tenant_id', 'group_id'], unique=False)

    # Add group_id and source_metadata to chunks table
    op.add_column('chunks', sa.Column('group_id', sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")))
    op.add_column('chunks', sa.Column('source_metadata', sa.Text(), nullable=True))
    
    op.create_foreign_key('fk_chunks_group_id', 'chunks', 'groups', ['group_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_chunks_bot_tenant_group', 'chunks', ['bot_id', 'tenant_id', 'group_id'], unique=False)
    op.create_index('idx_chunks_group_id', 'chunks', ['group_id'], unique=False)
    # Note: HNSW index for (tenant_id, group_id, vector) should be created in a separate migration
    # This requires: CREATE INDEX idx_chunks_tenant_group_vector ON chunks USING ivfflat (vector) WHERE tenant_id IS NOT NULL AND group_id IS NOT NULL


def downgrade() -> None:
    # Drop chunks changes
    op.drop_index('idx_chunks_bot_tenant_group', table_name='chunks')
    op.drop_index('idx_chunks_group_id', table_name='chunks')
    op.drop_constraint('fk_chunks_group_id', 'chunks', type_='foreignkey')
    op.drop_column('chunks', 'source_metadata')
    op.drop_column('chunks', 'group_id')

    # Drop documents changes
    op.drop_index('ix_documents_tenant_group', table_name='documents')
    op.drop_index('ix_documents_group_id', table_name='documents')
    op.drop_index('ix_documents_deleted', table_name='documents')
    op.drop_constraint('fk_documents_group_id', 'documents', type_='foreignkey')
    op.alter_column('documents', 'uploader_id', new_column_name='uploaded_by', existing_type=sa.Uuid(), nullable=True)
    op.drop_column('documents', 'deleted_at')
    op.drop_column('documents', 'group_id')

    # Drop bots changes
    op.drop_constraint('uq_bots_tenant_group_name', 'bots', type_='unique')
    op.drop_index('ix_bots_tenant_group', table_name='bots')
    op.drop_index('ix_bots_group_id', table_name='bots')
    op.drop_constraint('fk_bots_group_id', 'bots', type_='foreignkey')
    op.create_unique_constraint('uq_bots_tenant_name', 'bots', ['tenant_id', 'name'])
    op.drop_column('bots', 'group_id')

    # Drop group_members table
    op.drop_index('ix_group_members_user_id', table_name='group_members')
    op.drop_index('ix_group_members_group_user', table_name='group_members')
    op.drop_index('ix_group_members_group_id', table_name='group_members')
    op.drop_table('group_members')

    # Drop groups table
    op.drop_index('ix_groups_tenant_name', table_name='groups')
    op.drop_index('ix_groups_tenant_id', table_name='groups')
    op.drop_table('groups')
