"""Add password reset fields to users table."""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_add_password_reset_fields'
down_revision = '006_add_groups_and_provenance'
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
