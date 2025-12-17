"""add public/chat presentation fields to bots

Revision ID: 010_add_bot_public_fields
Revises: 009_update_vector_dimensions
Create Date: 2025-12-17
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010_add_bot_public_fields'
down_revision = '009_update_vector_dimensions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('bots') as batch_op:
        batch_op.add_column(sa.Column('avatar_url', sa.String(length=512), nullable=True))
        batch_op.add_column(sa.Column('welcome_message', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.false()))

    # Ensure existing rows get default false and then drop server_default to rely on ORM default
    op.execute("UPDATE bots SET is_public = FALSE WHERE is_public IS NULL")
    with op.batch_alter_table('bots') as batch_op:
        batch_op.alter_column('is_public', server_default=None)


def downgrade() -> None:
    with op.batch_alter_table('bots') as batch_op:
        batch_op.drop_column('is_public')
        batch_op.drop_column('welcome_message')
        batch_op.drop_column('avatar_url')
