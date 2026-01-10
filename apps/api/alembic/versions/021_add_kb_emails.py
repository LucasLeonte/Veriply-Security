"""Add kb_emails table for email knowledge base storage

Revision ID: 021_add_kb_emails
Revises: 020_add_user_writing_styles
Create Date: 2026-01-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers
revision = '021_add_kb_emails'
down_revision = '020_add_user_writing_styles'
branch_labels = None
depends_on = None


def upgrade():
    # Create kb_emails table
    op.create_table(
        'kb_emails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('email_integrations.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('email_id', sa.String(), nullable=False),
        sa.Column('thread_id', sa.String(), nullable=True),
        
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('from_email', sa.String(255), nullable=True),
        sa.Column('to_emails', sa.Text(), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        
        sa.Column('embedding', Vector(768), nullable=True),
        sa.Column('email_metadata', postgresql.JSONB(), nullable=True),  # Renamed from 'metadata'
        
        sa.Column('status', sa.String(50), nullable=False, server_default='uploaded'),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('chunk_count', sa.String(), nullable=True),
        
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create indexes
    op.create_index('idx_kb_emails_tenant_group', 'kb_emails', 
                   ['tenant_id', 'group_id'])
    op.create_index('idx_kb_emails_integration', 'kb_emails', 
                   ['integration_id'])
    op.create_index('idx_kb_emails_status', 'kb_emails', 
                   ['status'])
    op.create_index('idx_kb_emails_email_id', 'kb_emails', 
                   ['email_id'])
    op.create_index('idx_kb_emails_sent_at', 'kb_emails', 
                   ['sent_at'])
    
    # Create vector index for similarity search
    op.execute("""
        CREATE INDEX idx_kb_emails_embedding 
        ON kb_emails 
        USING ivfflat (embedding vector_cosine_ops) 
        WITH (lists = 100);
    """)
    
    # Enable RLS
    op.execute("""
        ALTER TABLE kb_emails ENABLE ROW LEVEL SECURITY;
        
        CREATE POLICY kb_emails_tenant_isolation
        ON kb_emails
        USING (tenant_id::text = current_setting('app.current_tenant_id', TRUE));
    """)


def downgrade():
    op.drop_table('kb_emails')
