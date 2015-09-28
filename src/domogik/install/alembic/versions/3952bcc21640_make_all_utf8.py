"""make all utf8

Revision ID: 3952bcc21640
Revises: 33cdc3706e51
Create Date: 2015-09-25 11:55:46.207709

"""

# revision identifiers, used by Alembic.
revision = '3952bcc21640'
down_revision = '33cdc3706e51'

from alembic import op
import sqlalchemy as sa
from domogik.common.sql_schema import \
        Sensor, Device, Command, XplStat, DeviceParam, \
        SensorHistory, XplStatParam, XplCommand, \
        XplCommandParam, CommandParam, PluginConfig, \
        Person, Scenario, UserAccount


def upgrade():
    con = op.get_bind()
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(Sensor.__tablename__)) )
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(Device.__tablename__)) )
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(Command.__tablename__)) )
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(XplStat.__tablename__)) )
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(DeviceParam.__tablename__)) )
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(SensorHistory.__tablename__)) )
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(XplStatParam.__tablename__)) )
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(XplCommand.__tablename__)) )
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(XplCommandParam.__tablename__)) )
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(CommandParam.__tablename__)) )
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(PluginConfig.__tablename__)) )
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(Person.__tablename__)) )
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(Scenario.__tablename__)) )
    con.execute( sa.sql.text('ALTER TABLE {0} convert to character set utf8 collate utf8_general_ci'.format(UserAccount.__tablename__)) )
    pass


def downgrade():
    pass
