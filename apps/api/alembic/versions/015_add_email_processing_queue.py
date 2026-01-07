"""add_email_processing_queue_table

Revision ID: 015_add_email_processing_queue
Revises: 014_add_email_monitoring_rules
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '015_add_email_processing_queue'
down_revision = '014_add_email_monitoring_rules'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'email_processing_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('email_integrations.id'), nullable=False),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('email_monitoring_rules.id'), nullable=True),
        sa.Column('provider_message_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='queued'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    op.create_index('ix_email_processing_tenant_integration', 'email_processing_queue', ['tenant_id', 'integration_id'])
    op.create_unique_constraint('uq_processing_integration_provider', 'email_processing_queue', ['integration_id', 'provider_message_id'])

    # RLS
    op.execute("""
        ALTER TABLE email_processing_queue ENABLE ROW LEVEL SECURITY;
    """)

    op.execute("""
        CREATE POLICY email_processing_queue_tenant_isolation ON email_processing_queue
        USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid);
    """)


def downgrade() -> None:
    op.drop_table('email_processing_queue')
