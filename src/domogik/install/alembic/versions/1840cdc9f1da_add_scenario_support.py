"""Add scenario support

Revision ID: 1840cdc9f1da
Revises: 43e639a62c8b
Create Date: 2013-10-08 13:31:23.006754

"""

# revision identifiers, used by Alembic.
revision = '1840cdc9f1da'
down_revision = '43e639a62c8b'

from alembic import op
import sqlalchemy as sa
from domogik.common.sql_schema import \
	Scenario

def upgrade():
    op.create_table(Scenario.__tablename__,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(length=32), autoincrement=False, nullable=False),
        sa.Column('json', sa.UnicodeText(), nullable=False),
        sa.Column('disabled', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )

def downgrade():
    op.drop_table(Scenario.__tablename__)
