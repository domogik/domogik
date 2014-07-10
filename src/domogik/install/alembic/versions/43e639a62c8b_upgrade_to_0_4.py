"""upgrade to 0.4

Revision ID: 43e639a62c8b
Revises: None
Create Date: 2013-10-04 19:29:38.035576

"""

# revision identifiers, used by Alembic.
revision = '43e639a62c8b'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from domogik.common.sql_schema import \
	Sensor, Device, Command, XplStat, DeviceParam, \
	SensorHistory, XplStatParam, XplCommand, \
	XplCommandParam, CommandParam, PluginConfig

def upgrade():
    op.create_table(DeviceParam.__tablename__,
    	sa.Column('id', sa.Integer(), nullable=False),
    	sa.Column('device_id', sa.Integer(), nullable=False),
    	sa.Column('key', sa.Unicode(length=32), autoincrement=False, nullable=False),
    	sa.Column('value', sa.Unicode(length=255), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], [u'{0}.id'.format(Device.__tablename__)], ondelete='cascade'),
    	sa.PrimaryKeyConstraint('id'),
    	mysql_engine='InnoDB'
    )
    op.create_table(Sensor.__tablename__,
    	sa.Column('id', sa.Integer(), nullable=False),
    	sa.Column('device_id', sa.Integer(), nullable=False),
    	sa.Column('name', sa.Unicode(length=255), nullable=True),
    	sa.Column('reference', sa.Unicode(length=64), nullable=True),
    	sa.Column('data_type', sa.Unicode(length=32), nullable=False),
    	sa.Column('conversion', sa.Unicode(length=255), nullable=True),
    	sa.Column('last_value', sa.Unicode(length=32), nullable=True),
    	sa.Column('last_received', sa.Integer(), nullable=True),
        sa.Column('history_store', sa.Boolean(), nullable=False),
        sa.Column('history_max', sa.Integer(), nullable=True),
        sa.Column('history_expire', sa.Integer(), nullable=True),
        sa.Column('history_round', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], [u'{0}.id'.format(Device.__tablename__)], ondelete='cascade'),
    	sa.PrimaryKeyConstraint('id'),
    	mysql_engine='InnoDB'
    )
    op.create_table(Command.__tablename__,
    	sa.Column('id', sa.Integer(), nullable=False),
    	sa.Column('device_id', sa.Integer(), nullable=False),
    	sa.Column('name', sa.Unicode(length=255), nullable=False),
    	sa.Column('reference', sa.Unicode(length=64), nullable=True),
    	sa.Column('return_confirmation', sa.Boolean(), nullable=False),
    	sa.ForeignKeyConstraint(['device_id'], [u'{0}.id'.format(Device.__tablename__)], ondelete='cascade'),
    	sa.PrimaryKeyConstraint('id'),
    	mysql_engine='InnoDB'
    )
    op.create_table(XplStat.__tablename__,
    	sa.Column('id', sa.Integer(), nullable=False),
    	sa.Column('device_id', sa.Integer(), nullable=False),
	sa.Column('json_id', sa.Unicode(length=64), nullable=False),
    	sa.Column('name', sa.Unicode(length=64), nullable=False),
	sa.Column('schema', sa.Unicode(length=32), nullable=False),
    	sa.ForeignKeyConstraint(['device_id'], [u'{0}.id'.format(Device.__tablename__)], ondelete='cascade'),
    	sa.PrimaryKeyConstraint('id'),
    	mysql_engine='InnoDB'
    )
    op.create_table(SensorHistory.__tablename__,
	sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
    	sa.Column('sensor_id', sa.Integer(), nullable=False, index=True),
    	sa.Column('date', sa.DateTime(), nullable=False, index=True),
    	sa.Column('value_num', sa.Float(), nullable=True),
    	sa.Column('value_str', sa.Unicode(length=32), nullable=False),
    	sa.ForeignKeyConstraint(['sensor_id'], [u'{0}.id'.format(Sensor.__tablename__)], ondelete='cascade'),
    	sa.PrimaryKeyConstraint('id'),
    	mysql_engine='InnoDB'
    )
    op.create_table(XplStatParam.__tablename__,
	sa.Column('xplstat_id', sa.Integer(), nullable=False),
    	sa.Column('key', sa.Unicode(length=32), autoincrement=False, nullable=False),
    	sa.Column('value', sa.Unicode(length=255), nullable=True),
        sa.Column('static', sa.Boolean(), nullable=False),
        sa.Column('sensor_id', sa.Integer(), nullable=False),
        sa.Column('ignore_values', sa.Unicode(length=255), nullable=True),
        sa.Column('type', sa.Unicode(length=32), nullable=True),
        sa.ForeignKeyConstraint(['sensor_id'], [u'{0}.id'.format(Sensor.__tablename__)], ondelete='cascade'),
        sa.ForeignKeyConstraint(['xplstat_id'], [u'{0}.id'.format(XplStat.__tablename__)], ondelete='cascade'),
        sa.PrimaryKeyConstraint('xplstat_id', 'key'),
        mysql_engine='InnoDB'
    )
    op.create_table(XplCommand.__tablename__,
	sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
    	sa.Column('cmd_id', sa.Integer(), nullable=False),
    	sa.Column('json_id', sa.Unicode(length=64), nullable=False),
    	sa.Column('name', sa.Unicode(length=64), nullable=False),
    	sa.Column('schema', sa.Unicode(length=32), nullable=False),
    	sa.Column('stat_id', sa.Integer(), nullable=True),
    	sa.ForeignKeyConstraint(['cmd_id'], [u'{0}.id'.format(Command.__tablename__)], ondelete='cascade'),
    	sa.ForeignKeyConstraint(['device_id'], [u'{0}.id'.format(Device.__tablename__)], ondelete='cascade'),
    	sa.ForeignKeyConstraint(['stat_id'], [u'{0}.id'.format(XplStat.__tablename__)], ondelete='cascade'),
    	sa.PrimaryKeyConstraint('id'),
    	mysql_engine='InnoDB'
    )
    op.create_table(CommandParam.__tablename__,
    	sa.Column('cmd_id', sa.Integer(), nullable=False),
    	sa.Column('key', sa.Unicode(length=32), nullable=False),
    	sa.Column('data_type', sa.Unicode(length=32), nullable=False),
    	sa.Column('conversion', sa.Unicode(length=255), nullable=True),
    	sa.ForeignKeyConstraint(['cmd_id'], [u'{0}.id'.format(Command.__tablename__)], ondelete='cascade'),
    	sa.PrimaryKeyConstraint('cmd_id', 'key'),
    	mysql_engine='InnoDB'
    )
    op.create_table(XplCommandParam.__tablename__,
	sa.Column('xplcmd_id', sa.Integer(), nullable=False),
    	sa.Column('key', sa.Unicode(length=32), autoincrement=False, nullable=False),
    	sa.Column('value', sa.Unicode(length=255), nullable=True),
    	sa.ForeignKeyConstraint(['xplcmd_id'], [u'{0}.id'.format(XplCommand.__tablename__)], ondelete='cascade'),
    	sa.PrimaryKeyConstraint('xplcmd_id', 'key'),
    	mysql_engine='InnoDB'
    )
    op.drop_constraint('core_device_ibfk_1', Device.__tablename__, type_='foreignkey')
    op.drop_constraint('core_device_ibfk_2', Device.__tablename__, type_='foreignkey')
    op.drop_constraint('core_device_type_ibfk_1', 'core_device_type', type_='foreignkey')
    op.add_column(Device.__tablename__, sa.Column('client_id', sa.Unicode(length=80), nullable=False))
    op.drop_column(Device.__tablename__, u'device_usage_id')
    op.alter_column(Device.__tablename__, u'address',
               existing_type=mysql.VARCHAR(length=255),
               nullable=True)
    op.alter_column(PluginConfig.__tablename__, u'`key`',
               existing_type=sa.Unicode(length=30),
               type_=sa.Unicode(length=255))
    op.alter_column(PluginConfig.__tablename__, u'value',
               existing_type=mysql.VARCHAR(length=255),
               type_=sa.UnicodeText())
    op.drop_table(u'core_device_usage')
    op.drop_table(u'core_device_feature')
    op.drop_table(u'migrate_version')
    op.drop_table(u'core_device_technology')
    op.drop_table(u'core_device_feature_model')
    op.drop_table(u'core_device_type')

def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(u'core_device', u'address',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False)
    op.add_column(u'core_device', sa.Column(u'device_usage_id', mysql.VARCHAR(length=80), nullable=False))
    op.drop_column(u'core_device', 'client_id')
    op.create_table(u'core_device_type',
    sa.Column(u'id', mysql.VARCHAR(length=80), nullable=False),
    sa.Column(u'device_technology_id', mysql.VARCHAR(length=30), nullable=False),
    sa.Column(u'name', mysql.VARCHAR(length=80), nullable=False),
    sa.Column(u'description', mysql.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['device_technology_id'], [u'core_device_technology.id'], name=u'core_device_type_ibfk_1'),
    sa.PrimaryKeyConstraint(u'id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'core_device_feature_model',
    sa.Column(u'id', mysql.VARCHAR(length=80), nullable=False),
    sa.Column(u'name', mysql.VARCHAR(length=30), nullable=False),
    sa.Column(u'feature_type', mysql.ENUM(u'actuator', u'sensor'), nullable=False),
    sa.Column(u'device_type_id', mysql.VARCHAR(length=80), nullable=False),
    sa.Column(u'parameters', mysql.TEXT(), nullable=True),
    sa.Column(u'value_type', mysql.VARCHAR(length=30), nullable=False),
    sa.Column(u'stat_key', mysql.VARCHAR(length=30), nullable=True),
    sa.Column(u'return_confirmation', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['device_type_id'], [u'core_device_type.id'], name=u'core_device_feature_model_ibfk_1'),
    sa.PrimaryKeyConstraint(u'id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'core_device_technology',
    sa.Column(u'id', mysql.VARCHAR(length=30), nullable=False),
    sa.Column(u'name', mysql.VARCHAR(length=30), nullable=False),
    sa.Column(u'description', mysql.TEXT(), nullable=True),
    sa.PrimaryKeyConstraint(u'id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'migrate_version',
    sa.Column(u'repository_id', mysql.VARCHAR(length=250), nullable=False),
    sa.Column(u'repository_path', mysql.TEXT(), nullable=True),
    sa.Column(u'version', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint(u'repository_id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'core_device_feature',
    sa.Column(u'id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column(u'device_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column(u'device_feature_model_id', mysql.VARCHAR(length=80), nullable=True),
    sa.ForeignKeyConstraint(['device_feature_model_id'], [u'core_device_feature_model.id'], name=u'core_device_feature_ibfk_2'),
    sa.ForeignKeyConstraint(['device_id'], [u'core_device.id'], name=u'core_device_feature_ibfk_1'),
    sa.PrimaryKeyConstraint(u'id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table(u'core_device_usage',
    sa.Column(u'id', mysql.VARCHAR(length=80), nullable=False),
    sa.Column(u'name', mysql.VARCHAR(length=30), nullable=False),
    sa.Column(u'description', mysql.TEXT(), nullable=True),
    sa.Column(u'default_options', mysql.TEXT(), nullable=True),
    sa.PrimaryKeyConstraint(u'id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.drop_table(u'core_xplcommand_param')
    op.drop_table(u'core_command_param')
    op.drop_table(u'core_xplcommand')
    op.drop_table(u'core_xplstat_param')
    op.drop_table(u'core_sensor_history')
    op.drop_table(u'core_xplstat')
    op.drop_table(u'core_command')
    op.drop_table(u'core_sensor')
    op.drop_table(u'core_device_params')
    ### end Alembic commands ###
