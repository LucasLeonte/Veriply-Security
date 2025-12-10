"""create documents table

Revision ID: 003_create_documents
Revises: 002_bots_rls
Create Date: 2025-12-04 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_create_documents'
down_revision = '002_bots_rls'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('bot_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bots.id'), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('mime', sa.String(length=100), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('storage_path', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='uploaded'),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    op.create_index('ix_documents_tenant_id', 'documents', ['tenant_id'])
    op.create_index('ix_documents_bot_id', 'documents', ['bot_id'])

    # trigger to update updated_at
    op.execute('''
    CREATE OR REPLACE FUNCTION update_documents_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = now();
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    CREATE TRIGGER trigger_documents_updated_at
        BEFORE UPDATE ON documents
        FOR EACH ROW
        EXECUTE FUNCTION update_documents_updated_at();
    ''')


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trigger_documents_updated_at ON documents;")
    op.execute("DROP FUNCTION IF EXISTS update_documents_updated_at();")
    op.drop_index('ix_documents_bot_id', table_name='documents')
    op.drop_index('ix_documents_tenant_id', table_name='documents')
    op.drop_table('documents')
