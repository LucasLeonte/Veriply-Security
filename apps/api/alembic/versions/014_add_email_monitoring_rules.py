"""add_email_monitoring_rules_table

Revision ID: 014_add_email_monitoring_rules
Revises: 013_add_integration_credentials
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014_add_email_monitoring_rules'
down_revision = '013_add_integration_credentials'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create email_monitoring_rules table
    op.create_table(
        'email_monitoring_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('email_integrations.id'), nullable=False),
        sa.Column('bot_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bots.id'), nullable=False),
        sa.Column('folder_labels', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # list[str]
        sa.Column('include_keywords', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('exclude_keywords', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Indexes to speed up lookups
    op.create_index('ix_email_rules_tenant_integration_active_prio', 'email_monitoring_rules', ['tenant_id', 'integration_id', 'is_active', 'priority'])
    op.create_index('ix_email_rules_user_id', 'email_monitoring_rules', ['user_id'])
    op.create_index('ix_email_rules_bot_id', 'email_monitoring_rules', ['bot_id'])

    # RLS policy
    op.execute("""
        ALTER TABLE email_monitoring_rules ENABLE ROW LEVEL SECURITY;
    """)

    op.execute("""
        CREATE POLICY email_monitoring_rules_tenant_isolation ON email_monitoring_rules
        USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid);
    """)


def downgrade() -> None:
    op.drop_table('email_monitoring_rules')
