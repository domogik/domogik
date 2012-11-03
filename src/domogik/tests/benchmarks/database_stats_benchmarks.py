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
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


import getopt, sys
import datetime, time
from domogik.common.database import DbHelper, DbHelperException
from domogik.common.sql_schema import DeviceStats
from domogik.tests.unittests.database_test import make_ts
import benchmarks_config as config

_db = None
_device1 = None
_insert_data = True

def run_stats_filter(period_filter_list):
    """Run various filtering function on statistics values

    @param period_filter_list : A list of filter(s) we wish ('minute', 'hour', 'day', 'week', 'month', 'year')

    """
    print("Running stats filtering, with : %s" % period_filter_list)
    if _insert_data:
        remove_all_stats()
        init_required_data_for_stats()
        add_data(start_p=time.mktime(config.DATA_START_DATE), end_p=time.mktime(config.DATA_END_DATE),
                 insert_step=config.DATA_INSERT_STEP, key='keysample')
    else:
        # Just get device id that was used to record stats
        global _device1
        # All records have the same device id
        ds = _db._DbHelper__session.query(DeviceStats).first()
        _device1 = _db.get_device(ds.device_id)

    # Minutes
    start_p = time.mktime(config.MINUTE_START_PERIOD)
    end_p = time.mktime(config.MINUTE_END_PERIOD)
    if 'minute' in period_filter_list:
        print("Executing minute filter : period = %s / %s" % (datetime.datetime.utcfromtimestamp(start_p),
                                                              datetime.datetime.utcfromtimestamp(end_p)))
        start_t = time.time()
        results = _db.filter_stats_of_device_by_key(ds_key='keysample', ds_device_id=_device1.id, start_date_ts=start_p,
                                                    end_date_ts=end_p, step_used='minute', function_used='avg')
        print("\tExecution time = %s" % (time.time() - start_t))

    # Hours
    start_p = time.mktime(config.HOUR_START_PERIOD)
    end_p = time.mktime(config.HOUR_END_PERIOD)
    if 'hour' in period_filter_list:
        print("Executing hour filter : period = %s / %s" % (datetime.datetime.utcfromtimestamp(start_p),
                                                            datetime.datetime.utcfromtimestamp(end_p)))
        start_t = time.time()
        results = _db.filter_stats_of_device_by_key(ds_key='keysample', ds_device_id=_device1.id, start_date_ts=start_p,
                                                    end_date_ts=end_p, step_used='hour', function_used='avg')
        print("\tExecution time = %s" % (time.time() - start_t))

    # Days
    start_p = time.mktime(config.DAY_START_PERIOD)
    end_p = time.mktime(config.DAY_END_PERIOD)
    if 'day' in period_filter_list:
        print("Executing day filter : period = %s / %s" % (datetime.datetime.utcfromtimestamp(start_p),
                                                           datetime.datetime.utcfromtimestamp(end_p)))
        start_t = time.time()
        results = _db.filter_stats_of_device_by_key(ds_key='keysample', ds_device_id=_device1.id, start_date_ts=start_p,
                                                    end_date_ts=end_p, step_used='day', function_used='avg')
        print("\tExecution time = %s" % (time.time() - start_t))

    # Weeks
    start_p = time.mktime(config.WEEK_START_PERIOD)
    end_p = time.mktime(config.WEEK_END_PERIOD)
    if 'week' in period_filter_list:
        print("Executing week filter : period = %s / %s" % (datetime.datetime.utcfromtimestamp(start_p),
                                                            datetime.datetime.utcfromtimestamp(end_p)))
        start_t = time.time()
        results = _db.filter_stats_of_device_by_key(ds_key='keysample', ds_device_id=_device1.id, start_date_ts=start_p,
                                                    end_date_ts=end_p, step_used='week', function_used='avg')
        print("\tExecution time = %s" % (time.time() - start_t))

    # Months
    start_p = time.mktime(config.MONTH_START_PERIOD)
    end_p = time.mktime(config.MONTH_END_PERIOD)
    if 'month' in period_filter_list:
        print("Executing month filter : period = %s / %s" % (datetime.datetime.utcfromtimestamp(start_p),
                                                             datetime.datetime.utcfromtimestamp(end_p)))
        start_t = time.time()
        results =  _db.filter_stats_of_device_by_key(ds_key='keysample', ds_device_id=_device1.id, start_date_ts=start_p,
                                                     end_date_ts=end_p, step_used='month', function_used='avg')
        print("\tExecution time = %s" % (time.time() - start_t))

    # Years
    start_p = time.mktime(config.YEAR_START_PERIOD)
    end_p = time.mktime(config.YEAR_END_PERIOD)
    if 'year' in period_filter_list:
        print("Executing year filter : period = %s / %s" % (datetime.datetime.utcfromtimestamp(start_p),
                                                            datetime.datetime.utcfromtimestamp(end_p)))
        start_t = time.time()
        results=  _db.filter_stats_of_device_by_key(ds_key='keysample', ds_device_id=_device1.id, start_date_ts=start_p,
                                                    end_date_ts=end_p, step_used='year', function_used='avg')
        print("Execution time = %s" % (time.time() - start_t))

def add_data(start_p, end_p, insert_step, key):
    """Add sample data into the database

    @param start_p  : start date (timestamp)
    @param end_p    : end date (timestamp)
    @insert_step    : step used when adding data (in secs)
    @key            : key name to insert

    """

    print("Inserting sample stats data, period = %s / %s, step = %s secs (%s values)" \
           % (datetime.datetime.utcfromtimestamp(start_p), datetime.datetime.utcfromtimestamp(end_p), insert_step,
              (end_p - start_p) / insert_step))
    conn = _db._DbHelper__engine.connect()
    ds_table = DeviceStats.__table__
    count = 0
    start_t = time.time()
    for i in range(0, int(end_p - start_p), insert_step):
        count += 1
        cur_date = start_p + i
        ins = ds_table.insert().values(date=datetime.datetime.utcfromtimestamp(cur_date), timestamp=cur_date,
                                       key=u'val', value=i/insert_step, value_num=i/insert_step, device_id=_device1.id)
        conn.execute(ins)
        """
        if (count % 50000 == 0):
            print("\t%s values inserted, date = %s" % (count, datetime.datetime.utcfromtimestamp(cur_date)),)
        """
    print("\t%s values inserted" % count)
    print("\tExecution time = %s" % (time.time() - start_t))

def init_required_data_for_stats():
    """Add pre-required data to build stats samples (eg. device)"""
    print(init_required_data_for_stats.__doc__)
    global _device1
    dt1 = _db.add_device_technology('x10', 'x10', 'this is x10')
    dty1 = _db.add_device_type(dty_id='x10.switch', dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
    du1 = _db.add_device_usage('lighting', 'Lighting')
    area1 = _db.add_area('area1','description 1')
    room1 = _db.add_room('room1', area1.id)
    _device1 = _db.add_device(d_name='device1', d_address = "A1", d_type_id = dty1.id, d_usage_id = du1.id)


def remove_all_stats():
    """Remove all existing data"""
    print("Removing existing data")
    engine = _db._DbHelper__engine
    ds_table = DeviceStats.__table__
    print("\tdropping DeviceStats table")
    ds_table.drop(bind=engine)
    print("\tcreating DeviceStats table")
    ds_table.create(bind=engine)

    for dt in _db.list_device_technologies():
        _db.del_device_technology(dt.id, cascade_delete=True)
    _db._DbHelper__session.commit()

def check_args(argv):
    """Check arguments passed to the program"""


def usage(prog_name):
    """Print program usage"""
    print("Usage : %s [-s [all|minute[,hour][,day][,week][,month[,year]]] [-I]" % prog_name)
    print("-s, --statistics=STATS_LIST\tSTATS_LIST can be : all or minute,hours,day,week,month,year")
    print("-I, --noinsert\t\t\tUse existing data in the database")

if __name__ == "__main__":
    stats_filter = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:I", ["help", "stats=", "noinsert"])
        _db = DbHelper(use_test_db=True)
        print("Using %s database" % _db.get_db_type())

        for opt, arg_list in opts:
            if opt in ("-s", "--stats"):
                possible_args = ['all', 'minute', 'hour', 'day', 'week', 'month', 'year']
                if arg_list is not None:
                    filter_list = arg_list.split(",")
                    # Check args are ok for -s option
                    for p_filter in filter_list:
                        if p_filter not in filter_list:
                            print("Wrong argument for statistics, must be one of : %s" % (",".join(possible_args)))
                            usage(sys.argv[0])
                    if 'all' in filter_list:
                        filter_list = possible_args[1:]
                    stats_filter = True
            elif opt in ("-h", "--help"):
                usage(sys.argv[0])
                sys.exit()
            elif opt in ("-I", "--noinsert"):
                _insert_data = False
            else:
                print("Unhandled option : %s" % opt)
                usage(sys.argv[0])
                sys.exit(2)
        if len(opts) == 0:
            usage(sys.argv[0])
            sys.exit(2)
        if stats_filter:
            run_stats_filter(filter_list)
    except getopt.GetoptError, err:
        print("Wrong arguments supplied : %s" % str(err))
        usage(sys.argv[0])
        sys.exit(2)
