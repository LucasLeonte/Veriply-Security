"""
Add monitoring and pause fields to email_integrations

Revision ID: 016_update_email_integrations_monitoring
Revises: 015_add_email_processing_queue
Create Date: 2026-01-07
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '016_update_email_integrations_monitoring'
down_revision = '015_add_email_processing_queue'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('email_integrations') as batch_op:
        batch_op.add_column(sa.Column('is_paused', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('last_poll_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_success_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_error_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_error_message', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('next_poll_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'))

    # Remove server defaults to keep application-level defaults only
    with op.batch_alter_table('email_integrations') as batch_op:
        batch_op.alter_column('is_paused', server_default=None)
        batch_op.alter_column('error_count', server_default=None)


def downgrade():
    with op.batch_alter_table('email_integrations') as batch_op:
        batch_op.drop_column('error_count')
        batch_op.drop_column('next_poll_at')
        batch_op.drop_column('last_error_message')
        batch_op.drop_column('last_error_at')
        batch_op.drop_column('last_success_at')
        batch_op.drop_column('last_poll_at')
        batch_op.drop_column('is_paused')
