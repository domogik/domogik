#!/usr/bin/env python
from migrate.versioning.shell import main
from domogik.common import database
_db = database.DbHelper()
main(url=_db.get_url_connection_string(), debug='False', repository='upgrade_repository')
