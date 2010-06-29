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

Plugin purpose
==============

Benchmarks for the database API

@author: Marc SCHNEIDER
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


import datetime, time
from domogik.common.database import DbHelper, DbHelperException
from domogik.common.sql_schema import DeviceStats
from domogik.tests.database_test import make_ts


_db = None
_device1 = None

def run_stats_filter(insert_data=True, **period_filter):
    """Run various filtering function on statistics values

    @param insert_data    : if False then don't insert sample data (default is True)
    @param *period_filter : A dictionnary of filter(s) we wish ('minute', 'hour', 'day', 'week', 'month', 'year')
                            Each item is set to True or False

    """
    # Minutes
    start_p = make_ts(2010, 1, 1, 15, 48, 0)
    end_p = make_ts(2010, 1, 31, 16, 8, 0)
    if (period_filter['minute'] or period_filter['hour']) and insert_data:
        save_data(start_p, end_p, 30, 'valmh')

    if period_filter['minute']:
        print "=====> Executing minute filter"
        start_t = time.time()
        results = _db.filter_stats_of_device_by_key(ds_key='valmh', ds_device_id=_device1.id, start_date_ts=start_p,
                                                    end_date_ts=end_p, step_used='minute', function_used='avg')
        print "Execution time = %s" % (time.time() - start_t)

    # Hours
    if period_filter['hour']:
        print "=====> Executing hour filter"
        start_t = time.time()
        results = _db.filter_stats_of_device_by_key(ds_key='valmh', ds_device_id=_device1.id, start_date_ts=start_p,
                                                    end_date_ts=end_p, step_used='hour', function_used='avg')
        print "Execution time = %s" % (time.time() - start_t)

    # Days
    start_p = make_ts(2010, 1, 1, 15, 4, 0)
    end_p = make_ts(2010, 12, 31, 21, 48, 0)
    if (period_filter['day'] or period_filter['week']) and insert_data:
        save_data(start_p, end_p, 28000, 'valdw')

    if period_filter['day']:
        print "=====> Executing day filter"
        start_t = time.time()
        results = _db.filter_stats_of_device_by_key(ds_key='valdw', ds_device_id=_device1.id, start_date_ts=start_p,
                                                    end_date_ts=end_p, step_used='day', function_used='avg')
        print "Execution time = %s" % (time.time() - start_t)

    # Weeks
    if period_filter['week']:
        print "=====> Executing week filter"
        start_t = time.time()
        results = _db.filter_stats_of_device_by_key(ds_key='valdw', ds_device_id=_device1.id, start_date_ts=start_p,
                                                    end_date_ts=end_p, step_used='week', function_used='avg')
        print "Execution time = %s" % (time.time() - start_t)

    # Months
    start_p = make_ts(2010, 6, 21, 15, 48, 0)
    end_p = make_ts(2020, 6, 21, 15, 48, 0)
    if (period_filter['month'] or period_filter['year']) and insert_data:
        save_data(start_p, end_p, 3600, 'valmy')

    if period_filter['month']:
        print "=====> Executing month filter"
        start_t = time.time()
        results =  _db.filter_stats_of_device_by_key(ds_key='valmy', ds_device_id=_device1.id, start_date_ts=start_p,
                                                     end_date_ts=end_p, step_used='month', function_used='avg')
        print "Execution time = %s" % (time.time() - start_t)

    # Years
    if period_filter['year']:
        print "=====> Executing year filter"
        start_t = time.time()
        results=  _db.filter_stats_of_device_by_key(ds_key='valmy', ds_device_id=_device1.id, start_date_ts=start_p,
                                                    end_date_ts=end_p, step_used='year', function_used='avg')
        print "Execution time = %s" % (time.time() - start_t)

def save_data(start_p, end_p, insert_step, key):
    """Store sample data into the database"""

    print "=====> Inserting data"
    count = 0
    for i in range(0, int(end_p - start_p), insert_step):
        count = count + 1
        _db._DbHelper__session.add(
            DeviceStats(date=datetime.datetime.utcfromtimestamp(start_p + i),
                        key=u'valmy', value=i/insert_step, device_id=_device1.id)
        )
    print "commiting..."
    _db._DbHelper__session.commit()
    print "%s values inserted" % count

def init_required_data_for_stats():

    """Add required data for stats (device)"""
    global _device1
    dt1 = _db.add_device_technology('x10', 'x10', 'this is x10')
    dty1 = _db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
    du1 = _db.add_device_usage("lighting")
    area1 = _db.add_area('area1','description 1')
    room1 = _db.add_room('room1', area1.id)
    _device1 = _db.add_device(d_name='device1', d_address = "A1", d_type_id = dty1.id, d_usage_id = du1.id)


def remove_all_stats():
    """Remove all existing data"""
    print "Removing existing data"
    for dt in _db.list_device_technologies():
        _db.del_device_technology(dt.id, cascade_delete=True)
    _db._DbHelper__session.query(DeviceStats).from_statement("DELETE FROM core_device_stats")
    """
    for ds in _db._DbHelper__session.query(DeviceStats).all():
        _db._DbHelper__session.delete(ds)
    """
    _db._DbHelper__session.commit()

if __name__ == "__main__":
    is_insert_data = True
    _db = DbHelper(use_test_db=True)
    if is_insert_data:
        remove_all_stats()
    init_required_data_for_stats()
    run_stats_filter(insert_data=is_insert_data, minute=False, hour=False, day=False, week=False, month=True, year=True)
