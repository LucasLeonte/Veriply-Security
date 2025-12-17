"""Create PII redactions table

Revision ID: 008_create_pii_redactions
Revises: 007_add_password_reset_fields
Create Date: 2025-12-16 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_create_pii_redactions'
down_revision = '007_add_password_reset_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create PII redactions table
    op.create_table(
        'pii_redactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('query_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bot_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bots.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        
        # Original encrypted
        sa.Column('original_query_encrypted', sa.LargeBinary(), nullable=False),
        sa.Column('encryption_iv', sa.LargeBinary(), nullable=False),  # 96-bit IV for GCM
        sa.Column('encryption_key_id', sa.String(length=100), nullable=True),
        
        # Redacted
        sa.Column('redacted_query', sa.Text(), nullable=False),
        
        # Redaction details (JSON)
        sa.Column('redactions', postgresql.JSONB(), nullable=False, server_default='[]'),
        
        # Audit
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accessed_count', sa.Integer(), nullable=False, server_default='0'),
    )
    
    # Create indexes for common queries
    op.create_index('idx_pii_redactions_query', 'pii_redactions', ['query_id'])
    op.create_index('idx_pii_redactions_bot_tenant', 'pii_redactions', ['bot_id', 'tenant_id'])
    op.create_index('idx_pii_redactions_created_at', 'pii_redactions', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_pii_redactions_created_at')
    op.drop_index('idx_pii_redactions_bot_tenant')
    op.drop_index('idx_pii_redactions_query')
    
    # Drop table
    op.drop_table('pii_redactions')
