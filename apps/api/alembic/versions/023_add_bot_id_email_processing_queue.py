"""
Add bot_id column to email_processing_queue

Revision ID: 023_add_bot_id_email_processing_queue
Revises: 022_add_user_id_email_processing_queue
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '023_add_bot_id_email_processing_queue'
down_revision = '022_add_user_id_email_processing_queue'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add nullable bot_id column to allow existing rows to remain valid
    op.add_column(
        'email_processing_queue',
        sa.Column('bot_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Create an index for faster lookups by bot
    op.create_index('ix_email_processing_bot_id', 'email_processing_queue', ['bot_id'])

    # Add foreign key constraint to bots(id)
    op.create_foreign_key(
        'fk_email_processing_queue_bot_id',
        'email_processing_queue',
        'bots',
        ['bot_id'],
        ['id'],
    )


def downgrade() -> None:
    # Remove FK, index, and column
    op.drop_constraint('fk_email_processing_queue_bot_id', 'email_processing_queue', type_='foreignkey')
    op.drop_index('ix_email_processing_bot_id', table_name='email_processing_queue')
    op.drop_column('email_processing_queue', 'bot_id')
