"""Create confidence_logs table for Story 3.4

Revision ID: 010_create_confidence_logs
Revises: 009_update_vector_dimensions
Create Date: 2025-12-17

Story 3.4: Confidence Scoring & Routing
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_create_confidence_logs'
down_revision = '009_update_vector_dimensions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create confidence_logs table."""
    # Create routing_decision enum type
    routing_decision_enum = postgresql.ENUM(
        'auto_send', 'hitl',
        name='routingdecision',
        create_type=True
    )
    routing_decision_enum.create(op.get_bind(), checkfirst=True)
    
    op.create_table(
        'confidence_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('bot_id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('query_id', sa.Uuid(), nullable=False),
        sa.Column('query_text', sa.String(500), nullable=True),
        
        # Confidence Components (0.000-1.000)
        sa.Column('retrieval_confidence', sa.Numeric(4, 3), nullable=False),
        sa.Column('source_consistency', sa.Numeric(4, 3), nullable=True),
        sa.Column('generation_confidence', sa.Numeric(4, 3), nullable=True),
        
        # Result
        sa.Column('overall_confidence', sa.Numeric(4, 3), nullable=False),
        sa.Column('threshold_used', sa.Numeric(4, 3), nullable=False),
        sa.Column(
            'routing_decision', 
            sa.Enum('auto_send', 'hitl', name='routingdecision'),
            nullable=False
        ),
        sa.Column('is_verified_kb', sa.String(10), server_default='false', nullable=False),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
    )
    
    # Create indexes for common queries
    op.create_index('ix_confidence_logs_bot_id', 'confidence_logs', ['bot_id'])
    op.create_index('ix_confidence_logs_tenant_id', 'confidence_logs', ['tenant_id'])
    op.create_index('ix_confidence_logs_routing', 'confidence_logs', ['bot_id', 'routing_decision'])
    op.create_index('ix_confidence_logs_created', 'confidence_logs', ['bot_id', 'created_at'])
    op.create_index('ix_confidence_logs_confidence', 'confidence_logs', ['overall_confidence'])


def downgrade() -> None:
    """Drop confidence_logs table."""
    op.drop_index('ix_confidence_logs_confidence', 'confidence_logs')
    op.drop_index('ix_confidence_logs_created', 'confidence_logs')
    op.drop_index('ix_confidence_logs_routing', 'confidence_logs')
    op.drop_index('ix_confidence_logs_tenant_id', 'confidence_logs')
    op.drop_index('ix_confidence_logs_bot_id', 'confidence_logs')
    op.drop_table('confidence_logs')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS routingdecision")
