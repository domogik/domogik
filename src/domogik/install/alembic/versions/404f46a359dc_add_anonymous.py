"""add anonymous

Revision ID: 404f46a359dc
Revises: b16c5714678
Create Date: 2016-02-29 06:26:19.626195

"""

# revision identifiers, used by Alembic.
revision = '404f46a359dc'
down_revision = '4db99a451791'

from alembic import op
import sqlalchemy as sa
from domogik.common.database import DbHelper

def upgrade():
    db = DbHelper(use_cache=False)
    with db.session_scope():
        db.add_user_account_with_person('Anonymous', 'Anonymous', 'Rest', 'Anonymous')
    del db

    pass


def downgrade():
    # we ill never delte
    pass
