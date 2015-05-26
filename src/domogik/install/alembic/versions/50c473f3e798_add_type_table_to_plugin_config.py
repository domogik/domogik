"""add type table to plugin_config

Revision ID: 50c473f3e798
Revises: 14ebd5a1ef73
Create Date: 2015-05-19 09:27:03.386497

"""

# revision identifiers, used by Alembic.
revision = '50c473f3e798'
down_revision = '14ebd5a1ef73'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.add_column('core_plugin_config', sa.Column('type', sa.Unicode(length=30), nullable=False, server_default=u'plugin'))
    op.drop_constraint('PRIMARY', 'core_plugin_config', type_='primary')
    op.create_primary_key('prim', 'core_plugin_config', ['id', 'type', 'hostname', 'key']) 


def downgrade():
    op.drop_column('core_plugin_config', 'type')
