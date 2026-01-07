"""add integration credentials table

Revision ID: 013_add_integration_credentials
Revises: 012_add_email_integrations
Create Date: 2026-01-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '013_add_integration_credentials'
down_revision = '012_add_email_integrations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'integration_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('encrypted_client_secret', sa.String(), nullable=False),
        sa.Column('redirect_uri', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    op.create_index('ix_integration_credentials_tenant_provider', 'integration_credentials', ['tenant_id', 'provider'])
    op.create_index('ix_integration_credentials_provider', 'integration_credentials', ['provider'])

    op.execute("""
        ALTER TABLE integration_credentials ENABLE ROW LEVEL SECURITY;
    """)

    op.execute("""
        CREATE POLICY integration_credentials_tenant_isolation ON integration_credentials
        USING (
            tenant_id IS NULL
            OR tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid
        );
    """)


def downgrade() -> None:
    op.drop_table('integration_credentials')