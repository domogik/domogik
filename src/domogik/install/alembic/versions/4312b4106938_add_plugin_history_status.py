"""add_plugin_history_status

Revision ID: 4312b4106938
Revises: 3ad7bd51bb91
Create Date: 2019-01-21 18:31:52.929537

"""

# revision identifiers, used by Alembic.
revision = '4312b4106938'
down_revision = '3ad7bd51bb91'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands adjusted ###
    print(u"Create new core_plugin table")
    op.create_table('core_plugin',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column('name', sa.Unicode(length=30), nullable=False, primary_key=True, autoincrement=False),
        sa.Column('type', sa.Unicode(length=30), nullable=False),
        sa.Column('hostname', sa.Unicode(length=40), nullable=False),
    #    sa.PrimaryKeyConstraint('id', 'name', 'type', 'hostname'),
        mysql_character_set='utf8',
        mysql_engine='InnoDB'
    )
    print(u"Create new core_plugin_history table")
    op.create_table('core_plugin_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plugin_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Unicode(length=30), nullable=True),
        sa.Column('comment', sa.UnicodeText(), nullable=True),
        sa.ForeignKeyConstraint(['plugin_id'], ['core_plugin.id'], ondelete='cascade'),
        sa.PrimaryKeyConstraint('id'),
        mysql_character_set='utf8',
        mysql_engine='InnoDB'
    )
    print(u"Create new index for core_plugin_history date columns")
    op.create_index(op.f('ix_core_plugin_history_date'), 'core_plugin_history', ['date'], unique=False)
    op.create_index('siddate', 'core_plugin_history', ['plugin_id', 'date'], unique=False)

    print(u"Rename core_plugin_config column id to name")
    #ALTER TABLE `core_plugin_config` CHANGE `id` `name` VARCHAR(30) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL;
    op.execute("ALTER TABLE core_plugin_config DROP PRIMARY KEY") # TODO TO Confirm
    op.alter_column(u"core_plugin_config", u"id", new_column_name="name", existing_type= sa.Unicode(length=30))

    print(u"Insert plugin ref to core_plugin table, filter dulplicate rule on columns type, id, hostname from core_plugin_config")
    op.execute("INSERT INTO core_plugin (type, name, hostname) SELECT DISTINCT type, name, hostname FROM core_plugin_config")
    print(u"Copie core_plugin_config structure to core_plugin_config_2 for creating new plugin_id column linked to core_plugin table")
    op.execute("CREATE TABLE core_plugin_config_2 LIKE core_plugin_config")

    print(u"Add new column plugin_id and index for core_plugin_config_2")
    op.execute("ALTER TABLE core_plugin_config_2 ADD plugin_id INT NOT NULL FIRST, ADD INDEX (plugin_id)")
    #op.add_column(u'core_plugin_config_2', sa.Column('plugin_id', sa.Integer(), nullable=False))
    op.create_foreign_key('core_plugin_config_ibfk_1', 'core_plugin_config_2', 'core_plugin', ['plugin_id'], ['id'], ondelete='cascade')

    print(u"Copie core_plugin_config datas into core_plugin_config_2 and set plugin_id relative to core_plugin plugin id")
    op.execute("INSERT INTO core_plugin_config_2 SELECT (SELECT id FROM core_plugin WHERE core_plugin.type=core_plugin_config.type AND core_plugin.name=core_plugin_config.name AND core_plugin.hostname=core_plugin_config.hostname), `name`, `type`, `hostname`, `key`, `value` FROM core_plugin_config")
    print(u"Remove core_plugin_config table")
    op.drop_table("core_plugin_config")
    print(u"rename core_plugin_config_2 to core_plugin_config")
    op.rename_table("core_plugin_config_2", "core_plugin_config")
    print(u"remove unused core_plugin_config columns")
    op.drop_column(u'core_plugin_config', 'hostname')
    op.drop_column(u'core_plugin_config', 'type')
    op.drop_column(u'core_plugin_config', 'name')
    ### end Alembic commands ###


def downgrade():
    ### commands adjusted ###
    print(u"Add Columns to core_plugin_config")
    op.add_column(u'core_plugin_config', sa.Column('id', mysql.VARCHAR(length=30), nullable=False))
    op.add_column(u'core_plugin_config', sa.Column('type', mysql.VARCHAR(length=30), nullable=False))
    op.add_column(u'core_plugin_config', sa.Column('hostname', mysql.VARCHAR(length=40), nullable=False))
    print(u"Reorder Columns from core_plugin_config")
    print(u"   - Rename 'key' to 'key2' and 'value' to 'value2'")
    op.alter_column(u"core_plugin_config", u"key", new_column_name="key2", existing_type=mysql.VARCHAR(length=255))
    op.alter_column(u"core_plugin_config", u"value", new_column_name="value2", existing_type=sa.UnicodeText())
    print(u"   - Create 'key' and value' columns to order them at last")
    op.add_column(u'core_plugin_config', sa.Column('key', mysql.VARCHAR(length=255), nullable=False))
    op.add_column(u'core_plugin_config', sa.Column('value', sa.UnicodeText(), nullable=False))
    print(u"   - copy 'key2' and value2' columns values to new columns")
    op.execute("UPDATE core_plugin_config SET core_plugin_config.key = core_plugin_config.key2, core_plugin_config.value = core_plugin_config.value2")
    print(u"   - delete 'key2' and value2' columns (end reorder)")
    op.drop_column(u'core_plugin_config', 'key2')
    op.drop_column(u'core_plugin_config', 'value2')
    print(u"Update new colomns value from core_plugin table")
    op.execute("UPDATE core_plugin_config, core_plugin SET core_plugin_config.id = core_plugin.name, core_plugin_config.type = core_plugin.type, core_plugin_config.hostname = core_plugin.hostname WHERE core_plugin_config.plugin_id = core_plugin.id")
    print(u"Remove constraint and colomn plugin_id from core_plugin_config")
    op.drop_constraint('core_plugin_config_ibfk_1', 'core_plugin_config', type_='foreignkey')
    op.drop_column(u'core_plugin_config', 'plugin_id')
    print(u"Create primary keys for core_plugin_config table")
    op.create_primary_key(constraint_name=None, table_name='core_plugin_config', columns=['id', 'type', 'hostname', 'key'])
    print(u"Remove core_plugin_history and core_plugin table")
    op.drop_table('core_plugin_history')
    op.drop_table('core_plugin')
    ### end Alembic commands ###
