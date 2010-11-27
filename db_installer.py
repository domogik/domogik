#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Module purpose
==============

Install the Domogik database based on config file values

Implements
==========


@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2010 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import getopt, sys

from sqlalchemy import create_engine

from domogik.common import sql_schema
from domogik.common import database
from domogik.common.configloader import Loader


###
# Installer
###

def install(create_prod_db, create_test_db):
    db = database.DbHelper()
    print "Using database", db.get_db_type()
    url = db.get_url_connection_string()

    # For unit tests
    if create_test_db:
        print "Creating test database..."
        test_url = '%s_test' % url
        engine_test = create_engine(test_url)
        sql_schema.metadata.create_all(engine_test)

    if not create_prod_db:
        return

    # Production database
    print "Creating production database..."
    engine = create_engine(url)
    sql_schema.metadata.create_all(engine)

    # Initialize default system configuration
    db.update_system_config()

    # Create a default user account
    db.add_default_user_account()

    # Create device usages
    db.add_device_usage(du_id='light', du_name='Light', du_description='Lamp, light usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_id='appliance', du_name='Appliance', du_description='Appliance usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_id='shutter', du_name='Shutter', du_description='Shutter usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Down&quot;, &quot;state1&quot;:&quot;Up&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_id='air_conditionning', du_name='Air conditioning', du_description='Air conditioning usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:1, &quot;unit&quot;:&quot;&amp;deg;C&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_id='ventilation', du_name='Ventilation', du_description='Ventilation usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_id='heating', du_name='Heating', du_description='Heating',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:1, &quot;unit&quot;:&quot;&amp;deg;C&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_id='computer', du_name='Computer', du_description='Desktop computer usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_id='server', du_name='Server', du_description='Server usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_id='telephony', du_name='Telephony', du_description='Phone usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } } ')
    db.add_device_usage(du_id='tv', du_name='TV', du_description='Television usage',
                    du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_id='water', du_name='Water', du_description='Water service',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    db.add_device_usage(du_id='gas', du_name='Gas', du_description='Gas service',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    db.add_device_usage(du_id='electricity', du_name='Electricity', du_description='Electricity service',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    db.add_device_usage(du_id='temperature', du_name='Temperature', du_description='Temperature',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {&quot;unit&quot;:&quot;&amp;deg;C&quot;}, &quot;string&quot;: {} }}')
    db.add_device_usage(du_id='mirror', du_name='Mir:ror', du_description='Mir:ror device',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    db.add_device_usage(du_id='nanoztag', du_name='Nanoztag', du_description='Nanoztag device',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')

def usage():
    print("Usage : db_installer [-t, --test] [-P, --no-prod]")
    print("-t or --test : database for unit tests will created (default is False)")
    print("-P or --no-prod : no production database will be created (default is True)")

if __name__ == "__main__":
    create_prod_db = True
    create_test_db = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hPt", ["help", "no-prod", "test"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-P', '--no-prod'):
            create_prod_db = False
        elif opt in ('-t', '--test'):
            create_test_db = True
    if not create_test_db and not create_prod_db:
        print "You must create either a production database or a test database"
        usage()
        sys.exit(2)
    install(create_prod_db, create_test_db)
