"""Add index to sensor_history

Revision ID: 3cccaa2ee819
Revises: e21aed8a6c73
Create Date: 2017-11-06 14:00:19.153218

"""

# revision identifiers, used by Alembic.
revision = '3cccaa2ee819'
down_revision = 'e21aed8a6c73'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.create_index('siddate', 'core_sensor_history', ['sensor_id', 'date'], unique=False)


def downgrade():
    op.drop_index('siddate', table_name='core_sensor_history')
