"""Add password reset fields to users table."""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add password reset token and expiration columns
    op.add_column('users', sa.Column('password_reset_token', sa.String, nullable=True))
    op.add_column('users', sa.Column('password_reset_expires', sa.DateTime, nullable=True))


def downgrade() -> None:
    # Remove password reset columns
    op.drop_column('users', 'password_reset_expires')
    op.drop_column('users', 'password_reset_token')
