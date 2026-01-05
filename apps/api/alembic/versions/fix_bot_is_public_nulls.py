"""Fix NULL is_public values in bots table.

Revision ID: fix_bot_is_public_nulls
Revises: 
Create Date: 2025-12-17 13:56:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_bot_is_public_nulls'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Set NULL is_public values to False."""
    op.execute(
        sa.text("UPDATE bots SET is_public = FALSE WHERE is_public IS NULL")
    )


def downgrade() -> None:
    """No downgrade needed - data preservation."""
    pass
