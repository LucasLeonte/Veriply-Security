"""Add user_email_history table for writing style analysis

Revision ID: 019_add_user_email_history
Revises: 018_add_bot_is_active
Create Date: 2026-01-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '019_add_user_email_history'
down_revision = '018_add_bot_is_active'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_email_history table
    op.create_table(
        'user_email_history',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=False),
        sa.Column('integration_id', postgresql.UUID(), nullable=False),
        sa.Column('email_id', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('analyzed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['integration_id'], ['email_integrations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_user_email_history_tenant_user', 'user_email_history', 
                    ['tenant_id', 'user_id'], unique=False)
    op.create_index('idx_user_email_history_integration', 'user_email_history', 
                    ['integration_id'], unique=False)
    op.create_index('idx_user_email_history_analyzed', 'user_email_history', 
                    ['analyzed'], unique=False)
    
    # Create unique constraint to prevent duplicate emails from periodic syncs
    op.create_unique_constraint('uq_email_id_per_integration', 'user_email_history',
                                ['integration_id', 'email_id'])
    
    # Enable RLS
    op.execute('''
        ALTER TABLE user_email_history ENABLE ROW LEVEL SECURITY;
        
        CREATE POLICY user_email_history_tenant_isolation
        ON user_email_history
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);
    ''')


def downgrade() -> None:
    op.drop_table('user_email_history')
