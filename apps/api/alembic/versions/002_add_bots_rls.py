"""add bots table RLS policies

Revision ID: 002_bots_rls
Revises: 001_create_bots
Create Date: 2025-12-04 10:00:01.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '002_bots_rls'
down_revision = '001_create_bots'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable RLS on bots table
    op.execute("ALTER TABLE bots ENABLE ROW LEVEL SECURITY;")
    
    # Policy: Users can only see bots from their own tenant
    op.execute("""
        CREATE POLICY bots_tenant_isolation ON bots
            FOR ALL
            USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    """)
    
    # Policy: Allow service role to bypass RLS (for background jobs, migrations, etc.)
    op.execute("""
        CREATE POLICY bots_service_role ON bots
            FOR ALL
            TO service_role
            USING (true);
    """)


def downgrade() -> None:
    # Drop policies
    op.execute("DROP POLICY IF EXISTS bots_service_role ON bots;")
    op.execute("DROP POLICY IF EXISTS bots_tenant_isolation ON bots;")
    
    # Disable RLS
    op.execute("ALTER TABLE bots DISABLE ROW LEVEL SECURITY;")
