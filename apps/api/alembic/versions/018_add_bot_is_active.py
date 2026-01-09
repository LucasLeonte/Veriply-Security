"""add is_active field to bots

Revision ID: 018_add_bot_is_active
Revises: 017_add_verified_qa_edit_fields
Create Date: 2026-01-09
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '018_add_bot_is_active'
down_revision = '017_add_verified_qa_edit_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('bots') as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))

    # Ensure existing rows get default true and then drop server_default to rely on ORM default
    op.execute("UPDATE bots SET is_active = TRUE WHERE is_active IS NULL")
    with op.batch_alter_table('bots') as batch_op:
        batch_op.alter_column('is_active', server_default=None)


def downgrade() -> None:
    with op.batch_alter_table('bots') as batch_op:
        batch_op.drop_column('is_active')
