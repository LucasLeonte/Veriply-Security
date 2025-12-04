"""create bots table

Revision ID: 001_create_bots
Revises: 
Create Date: 2025-12-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_create_bots'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create bot_status enum type
    op.execute("""
        CREATE TYPE bot_status AS ENUM ('Empty', 'Processing', 'Ready');
    """)
    
    # Create bots table
    op.create_table(
        'bots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('confidence_threshold', sa.Integer(), nullable=False, server_default='80'),
        sa.Column('status', sa.Enum('Empty', 'Processing', 'Ready', name='bot_status'), nullable=False, server_default='Empty'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes
    op.create_index('ix_bots_tenant_id', 'bots', ['tenant_id'])
    op.create_index('ix_bots_tenant_created', 'bots', ['tenant_id', 'created_at'])
    
    # Create unique constraint on tenant_id + name
    op.create_unique_constraint('uq_bots_tenant_name', 'bots', ['tenant_id', 'name'])
    
    # Create trigger to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_bots_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER trigger_bots_updated_at
            BEFORE UPDATE ON bots
            FOR EACH ROW
            EXECUTE FUNCTION update_bots_updated_at();
    """)


def downgrade() -> None:
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS trigger_bots_updated_at ON bots;")
    op.execute("DROP FUNCTION IF EXISTS update_bots_updated_at();")
    
    # Drop table
    op.drop_table('bots')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS bot_status;")
