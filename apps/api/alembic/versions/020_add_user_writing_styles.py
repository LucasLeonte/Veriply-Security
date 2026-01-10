"""Add user_writing_styles table for storing user style profiles

Revision ID: 020_add_user_writing_styles
Revises: 019_add_user_email_history
Create Date: 2026-01-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '020_add_user_writing_styles'
down_revision = '019_add_user_email_history'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_writing_styles table
    op.create_table(
        'user_writing_styles',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=False),
        sa.Column('integration_id', postgresql.UUID(), nullable=False),
        sa.Column('tone', sa.String(20), nullable=False, server_default='semi_formal'),
        sa.Column('greeting_pattern', sa.String(100), nullable=True),
        sa.Column('closing_pattern', sa.String(100), nullable=True),
        sa.Column('avg_sentence_length', sa.Integer(), nullable=True),
        sa.Column('avg_email_length', sa.Integer(), nullable=True),
        sa.Column('uses_emojis', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('formality_score', sa.Integer(), nullable=False, server_default='65'),
        sa.Column('custom_preferences', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('is_manual_override', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('sample_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_analyzed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['integration_id'], ['email_integrations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'integration_id', 'tenant_id', name='uq_style_per_integration')
    )
    
    # Create indexes
    op.create_index('idx_user_writing_style_tenant_user', 'user_writing_styles',
                    ['tenant_id', 'user_id'], unique=False)
    op.create_index('idx_user_writing_style_integration', 'user_writing_styles',
                    ['integration_id'], unique=False)
    
    # Enable RLS
    op.execute('''
        ALTER TABLE user_writing_styles ENABLE ROW LEVEL SECURITY;
        
        CREATE POLICY user_writing_style_tenant_isolation
        ON user_writing_styles
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);
    ''')


def downgrade() -> None:
    op.drop_table('user_writing_styles')
