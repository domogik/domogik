from sqlalchemy import *
from migrate import *
from domogik.common.sql_schema import Page, Room, Area


def upgrade(migrate_engine):
    # bind the engine
    meta = MetaData(bind=migrate_engine)

    # create the new table
    page = Page.__table__
    page.create(bind=migrate_engine)

    # insert the root element
    page.insert(name='ROOT', left=1, right=2, description='', icon='')

    # TODO transfere the data

    # DO NOT DROP the room and area tables
    # Drop the old room table
    # room = Table(Room.__tablename__, meta)
    # meta.drop( room )
    # Drop the old area table
    # area = Table(Area.__tablename__, meta)
    # meta.drop( area )

def downgrade(migrate_engine):
    # bind the engine
    meta = MetaData(bind=migrate_engine)
    # NOT dropped so not needed
    # recreate the room table
    #room = Table(Room.__tablename__, meta)
    #meta.create( room )
    # recreate the area table
    #area = Table(Area.__tablename__, meta)
    #meta.create( area )
    
    # TODO transfere the data

    # drop the page table
    page = Table(Page.__tablename__, meta)
    page.drop()
