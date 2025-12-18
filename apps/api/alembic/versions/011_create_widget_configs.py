"""create widget_configs table

Revision ID: 011_create_widget_configs
Revises: 010_add_bot_public_fields
Create Date: 2025-12-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011_create_widget_configs'
down_revision = '010_add_bot_public_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:\n    op.create_table(
        'widget_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('bot_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('position', sa.String(length=20), nullable=False, server_default='bottom-right'),
        sa.Column('primary_color', sa.String(length=7), nullable=False, server_default='#3B82F6'),
        sa.Column('welcome_message', sa.String(length=200), nullable=True),
        sa.Column('auto_open', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('bot_id', name='uq_widget_config_bot_id'),
    )


def downgrade() -> None:
    op.drop_table('widget_configs')
