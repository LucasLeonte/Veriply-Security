"""Update group roles to unified organization roles

Revision ID: 015_update_group_roles
Revises: 014_add_tenant_invite_fields
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '015_update_group_roles'
down_revision = '014_add_tenant_invite_fields'
branch_labels = None
depends_on = None


def upgrade():
    # PostgreSQL doesn't allow direct enum modification, so we need to:
    # 1. Add new enum values
    # 2. Update existing data
    # 3. Remove old enum values
    
    # First, create a new enum type with the unified roles
    op.execute("CREATE TYPE grouprole_new AS ENUM ('owner', 'admin', 'manager', 'agent', 'viewer')")
    
    # Update the column to use the new enum type, with value mapping
    op.execute("""
        ALTER TABLE group_members 
        ALTER COLUMN role TYPE grouprole_new 
        USING (
            CASE role::text
                WHEN 'group_admin' THEN 'owner'::grouprole_new
                WHEN 'manager' THEN 'manager'::grouprole_new
                WHEN 'operator' THEN 'viewer'::grouprole_new
            END
        )
    """)
    
    # Drop the old enum type
    op.execute("DROP TYPE grouprole")
    
    # Rename the new enum type to the original name
    op.execute("ALTER TYPE grouprole_new RENAME TO grouprole")


def downgrade():
    # Reverse the process
    op.execute("CREATE TYPE grouprole_old AS ENUM ('group_admin', 'manager', 'operator')")
    
    op.execute("""
        ALTER TABLE group_members 
        ALTER COLUMN role TYPE grouprole_old 
        USING (
            CASE role::text
                WHEN 'owner' THEN 'group_admin'::grouprole_old
                WHEN 'admin' THEN 'manager'::grouprole_old
                WHEN 'manager' THEN 'manager'::grouprole_old
                WHEN 'agent' THEN 'operator'::grouprole_old
                WHEN 'viewer' THEN 'operator'::grouprole_old
            END
        )
    """)
    
    op.execute("DROP TYPE grouprole")
    op.execute("ALTER TYPE grouprole_old RENAME TO grouprole")
