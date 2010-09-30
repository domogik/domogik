#!/usr/bin/python
# -*- coding: utf-8 -*-

# Test data that will be inserted into the database
# Format is : (year, month, day, hours, minutes, seconds, 0, 0, 0)
# Three last numbers aren't used leave them to 0
DATA_START_DATE = (2010, 1, 1, 15, 48, 0, 0, 0, 0)
DATA_END_DATE = (2010, 4, 1, 15, 48, 0, 0, 0, 0)
DATA_INSERT_STEP = 30 # in seconds

# Analysed period : minutes
MINUTE_START_PERIOD = (2010, 1, 1, 15, 48, 0, 0, 0, 0)
MINUTE_END_PERIOD = (2010, 3, 31, 16, 8, 0, 0, 0, 0)

# Analysed period : hours
HOUR_START_PERIOD = (2010, 1, 1, 15, 48, 0, 0, 0, 0)
HOUR_END_PERIOD = (2010, 3, 31, 16, 8, 0, 0, 0, 0)

# Analysed period : days
DAY_START_PERIOD = (2010, 1, 1, 15, 48, 0, 0, 0, 0)
DAY_END_PERIOD = (2010, 3, 31, 16, 8, 0, 0, 0, 0)

# Analysed period : weeks
WEEK_START_PERIOD = (2010, 1, 1, 15, 48, 0, 0, 0, 0)
WEEK_END_PERIOD = (2010, 3, 31, 16, 8, 0, 0, 0, 0)

# Analysed period : months
MONTH_START_PERIOD = (2010, 1, 1, 15, 48, 0, 0, 0, 0)
MONTH_END_PERIOD = (2010, 9, 31, 16, 8, 0, 0, 0, 0)

# Analysed period : years
YEAR_START_PERIOD = (2010, 1, 1, 15, 48, 0, 0, 0, 0)
YEAR_END_PERIOD = (2012, 3, 31, 16, 8, 0, 0, 0, 0)
