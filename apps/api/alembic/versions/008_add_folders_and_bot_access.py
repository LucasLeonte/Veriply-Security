"""Add folders and bot_document_access tables for group KB organization and bot-level access control.

Revision ID: 008_add_folders_and_bot_access
Revises: 007_add_password_reset_fields
Create Date: 2025-12-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008_add_folders_and_bot_access'
down_revision = '007_add_password_reset_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create folders table
    op.create_table(
        'folders',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('group_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'group_id', 'name', name='uq_folders_tenant_group_name'),
    )
    op.create_index('ix_folders_tenant_id', 'folders', ['tenant_id'], unique=False)
    op.create_index('ix_folders_group_id', 'folders', ['group_id'], unique=False)
    op.create_index('ix_folders_tenant_group', 'folders', ['tenant_id', 'group_id'], unique=False)
    op.create_index('ix_folders_deleted', 'folders', ['deleted_at'], unique=False)

    # Add folder_id to documents table
    op.add_column('documents', sa.Column('folder_id', sa.Uuid(), nullable=True))
    op.create_foreign_key('fk_documents_folder_id', 'documents', 'folders', ['folder_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_documents_folder_id', 'documents', ['folder_id'], unique=False)

    # Create bot_document_access table
    op.create_table(
        'bot_document_access',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('group_id', sa.Uuid(), nullable=False),
        sa.Column('bot_id', sa.Uuid(), nullable=False),
        sa.Column('document_id', sa.Uuid(), nullable=True),
        sa.Column('folder_id', sa.Uuid(), nullable=True),
        sa.Column('is_allowed', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bot_id', 'document_id', name='uq_bot_document_access_bot_document'),
        sa.UniqueConstraint('bot_id', 'folder_id', name='uq_bot_document_access_bot_folder'),
        sa.CheckConstraint(
            '(document_id IS NOT NULL AND folder_id IS NULL) OR (document_id IS NULL AND folder_id IS NOT NULL)',
            name='chk_bot_document_access_one_target'
        ),
    )
    op.create_index('ix_bot_document_access_tenant_id', 'bot_document_access', ['tenant_id'], unique=False)
    op.create_index('ix_bot_document_access_group_id', 'bot_document_access', ['group_id'], unique=False)
    op.create_index('ix_bot_document_access_tenant_group', 'bot_document_access', ['tenant_id', 'group_id'], unique=False)
    op.create_index('ix_bot_document_access_bot_document', 'bot_document_access', ['bot_id', 'document_id'], unique=False)
    op.create_index('ix_bot_document_access_bot_folder', 'bot_document_access', ['bot_id', 'folder_id'], unique=False)


def downgrade() -> None:
    # Drop bot_document_access table
    op.drop_index('ix_bot_document_access_bot_folder', table_name='bot_document_access')
    op.drop_index('ix_bot_document_access_bot_document', table_name='bot_document_access')
    op.drop_index('ix_bot_document_access_tenant_group', table_name='bot_document_access')
    op.drop_index('ix_bot_document_access_group_id', table_name='bot_document_access')
    op.drop_index('ix_bot_document_access_tenant_id', table_name='bot_document_access')
    op.drop_table('bot_document_access')

    # Drop folder_id from documents
    op.drop_index('ix_documents_folder_id', table_name='documents')
    op.drop_constraint('fk_documents_folder_id', 'documents', type_='foreignkey')
    op.drop_column('documents', 'folder_id')

    # Drop folders table
    op.drop_index('ix_folders_deleted', table_name='folders')
    op.drop_index('ix_folders_tenant_group', table_name='folders')
    op.drop_index('ix_folders_group_id', table_name='folders')
    op.drop_index('ix_folders_tenant_id', table_name='folders')
    op.drop_table('folders')
