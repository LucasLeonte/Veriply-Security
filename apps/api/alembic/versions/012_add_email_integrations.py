"""add_email_integrations_table

Revision ID: 012_add_email_integrations
Revises: 011_sync_confidence_logs_schema
Create Date: 2025-12-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012_add_email_integrations'
down_revision = '011_sync_confidence_logs_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create email_integrations table
    op.create_table(
        'email_integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('encrypted_refresh_token', sa.String(), nullable=True),
        sa.Column('scope', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='connected'),
        sa.Column('last_sync_time', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    # Add indexes
    op.create_index('ix_email_integrations_tenant_id', 'email_integrations', ['tenant_id'])
    op.create_index('ix_email_integrations_user_id', 'email_integrations', ['user_id'])
    op.create_index('ix_email_integrations_provider', 'email_integrations', ['provider'])
    
    # Add RLS policy
    op.execute("""
        ALTER TABLE email_integrations ENABLE ROW LEVEL SECURITY;
    """)
    
    op.execute("""
        CREATE POLICY email_integrations_tenant_isolation ON email_integrations
        USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid);
    """)


def downgrade() -> None:
    op.drop_table('email_integrations')
