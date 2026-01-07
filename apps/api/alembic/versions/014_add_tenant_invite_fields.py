"""Add tenant invite fields to users for cross-tenant transfer.

Revision ID: 014_add_tenant_invite_fields
Revises: 012_update_widget_color_storage
Create Date: 2026-01-06 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '014_add_tenant_invite_fields'
down_revision = '012_update_widget_color_storage'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('tenant_invite_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('tenant_invite_expires', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('pending_tenant_id', sa.Uuid(), nullable=True))
    op.add_column('users', sa.Column('pending_role', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'pending_role')
    op.drop_column('users', 'pending_tenant_id')
    op.drop_column('users', 'tenant_invite_expires')
    op.drop_column('users', 'tenant_invite_token')
