"""Add user_id field to email_processing_queue for audit trail

Revision ID: 022_add_user_id_email_processing_queue
Revises: 021_add_kb_emails
Create Date: 2026-01-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '022_add_user_id_email_processing_queue'
down_revision = '021_add_kb_emails'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add user_id column after tenant_id
    op.add_column(
        'email_processing_queue',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, server_default='00000000-0000-0000-0000-000000000000')
    )
    
    # Remove the server default after population (since we can't know actual user_ids in bulk)
    op.alter_column('email_processing_queue', 'user_id', server_default=None)


def downgrade() -> None:
    op.drop_column('email_processing_queue', 'user_id')
