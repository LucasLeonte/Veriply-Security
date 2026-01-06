"""remove primary_color from bots, keep only in widget_configs

Revision ID: 012_update_widget_color_storage
Revises: 011_sync_confidence_logs_schema, 011_create_widget_configs, 011_update_confidence_logs
Create Date: 2025-01-05

Merge migration and remove primary_color from bots table.
Primary color should be stored in widget_configs (per-widget instance).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012_update_widget_color_storage'
down_revision = ('011_sync_confidence_logs_schema', '011_create_widget_configs', '011_update_confidence_logs')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check which columns exist before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    bots_columns = [col['name'] for col in inspector.get_columns('bots')]
    widget_configs_columns = [col['name'] for col in inspector.get_columns('widget_configs')]
    
    # Remove welcome_message and primary_color from bots (if they exist)
    with op.batch_alter_table('bots') as batch_op:
        if 'welcome_message' in bots_columns:
            batch_op.drop_column('welcome_message')
        if 'primary_color' in bots_columns:
            batch_op.drop_column('primary_color')
    
    # Remove welcome_message from widget_configs (if it exists)
    if 'welcome_message' in widget_configs_columns:
        with op.batch_alter_table('widget_configs') as batch_op:
            batch_op.drop_column('welcome_message')


def downgrade() -> None:
    with op.batch_alter_table('bots') as batch_op:
        batch_op.add_column(sa.Column('welcome_message', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('primary_color', sa.String(length=7), nullable=False, server_default='#3B82F6'))
    
    with op.batch_alter_table('widget_configs') as batch_op:
        batch_op.add_column(sa.Column('welcome_message', sa.String(length=200), nullable=True))
