#!/usr/bin/env python
"""

This module provides a class for cron-like scheduling systems, and
exposes the function used to convert static cron expressions to Python
sets.

CronExpression objects are instantiated with a cron formatted string
that represents the times when the trigger is active. When using
expressions that contain periodic terms, an extension of cron created
for this module, a starting epoch should be explicitly defined. When the
epoch is not explicitly defined, it defaults to the Unix epoch. Periodic
terms provide a method of recurring triggers based on arbitrary time
periods.


Standard Cron Triggers:
>>> job = CronExpression("0 0 * * 1-5/2 find /var/log -delete")
>>> job.check_trigger((2010, 11, 17, 0, 0))
True
>>> job.check_trigger((2012, 12, 21, 0 , 0))
False

Periodic Trigger:
>>> job = CronExpression("0 %9 * * * Feed 'it'", (2010, 5, 1, 7, 0, -6))
>>> job.comment
"Feed 'it'"
>>> job.check_trigger((2010, 5, 1, 7, 0), utc_offset=-6)
True
>>> job.check_trigger((2010, 5, 1, 16, 0), utc_offset=-6)
True
>>> job.check_trigger((2010, 5, 2, 1, 0), utc_offset=-6)
True
"""

import datetime
import calendar
import ephem
import re
import traceback

__all__ = ["CronExpression", "DEFAULT_EPOCH", "SUBSTITUTIONS"]
__license__ = "Public Domain"

DAY_NAMES = zip(('sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'), xrange(7))
MINUTES = (0, 59)
HOURS = (0, 23)
DAYS_OF_MONTH = (1, 31)
MONTHS = (1, 12)
DAYS_OF_WEEK = (0, 6)
YEARS = (2016, 2200)
L_FIELDS = (DAYS_OF_WEEK, DAYS_OF_MONTH)
FIELD_RANGES = (MINUTES, HOURS, DAYS_OF_MONTH, MONTHS, DAYS_OF_WEEK, YEARS)
MONTH_NAMES = zip(('jan', 'feb', 'mar', 'apr', 'may', 'jun',
                   'jul', 'aug', 'sep', 'oct', 'nov', 'dec'), xrange(1, 13))
DEFAULT_EPOCH = (1970, 1, 1, 0, 0, 0)
SUBSTITUTIONS = {
    "@yearly": "0 0 1 1 *",
    "@anually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *"
}

SPECIALS = [
    '@fullmoon', '@newmoon', '@firstquarter', '@lastquarter',
    '@equinox', '@solstice',
    '@dawn', '@dusk'
]

class CronExpression(object):
    def __init__(self, line, epoch=DEFAULT_EPOCH, epoch_utc_offset=0):
        """
        Instantiates a CronExpression object with an optionally defined epoch.
        If the epoch is defined, the UTC offset can be specified one of two
        ways: as the sixth element in 'epoch' or supplied in epoch_utc_offset.
        The epoch should be defined down to the minute sorted by
        descending significance.
        """
        self._valid = True
        self._special = False
        for key in SPECIALS:
            if line.startswith(key):
                self._special = True
                # build the city object
                self._city = ephem.city('Brussels')
        # store the original input
        self.orig_line = line

        # parse the input
        if not self._special:
            for key, value in SUBSTITUTIONS.items():
                if line.startswith(key):
                    line = line.replace(key, value)
                    break

            fields = line.split(' ')
            if len(fields) >= 6:
                if re.match( r'^(?:\*$)|(^\d{4}$)|(^\d{4}(([,-]?\d{4})|(/?\d))+$)', fields[5]) is not None :
                    # this a years field
                    fields = line.split(None, 6)
                else :
                    if re.match( r'(^\d{}$)|(^\d(([,-]?\d)|(/?\d))+$)', fields[5]) is not None :
                        # this a bad years field but keep it, raise should be arrive in computing
                        fields = line.split(None, 6)
                    else :
                        # add years all in field
                        fields = line.split(None, 5)
                        fields.insert(5, '*')
            else :
                fields = line.split(None, 5)
            if len(fields) == 5:
                # add years all in field
                fields.append('*')
            if len(fields) == 6:
                # add empty comment
                fields.append('')
            minutes, hours, dom, months, dow, years, self.comment = fields

            dow = dow.replace('7', '0').replace('?', '*')
            dom = dom.replace('?', '*')

            for monthstr, monthnum in MONTH_NAMES:
                months = months.lower().replace(monthstr, str(monthnum))

            for dowstr, downum in DAY_NAMES:
                dow = dow.lower().replace(dowstr, str(downum))

            self.string_tab = [minutes, hours, dom.upper(), months, dow.upper(), years]
            self.compute_numtab()
        else:
            self.string_tab = line.split(' ')[0]
            self.comment = None

        # handle epoch
        if len(epoch) == 5:
            y, mo, d, h, m = epoch
            self.epoch = (y, mo, d, h, m, epoch_utc_offset)
        else:
            self.epoch = epoch


    def __str__(self):
        if self.epoch != DEFAULT_EPOCH:
            return "{0}(\"{1}\", epoch=\"{2}\")".format(self.__class__.__name__, self.orig_line, repr(self.epoch))
        else:
            return "{0}(\"{1}\")".format(self.__class__.__name__, self.orig_line)

    def __repr__(self):
        return str(self)

    def isValidate(self):
        """
        Return True if cron expression is validate, else False
        """
        return self._valid

    def compute_numtab(self):
        """
        Recomputes the sets for the static ranges of the trigger time.

        This method should only be called by the user if the string_tab
        member is modified.
        """
        self.numerical_tab = []
        self._valid = True
        for field_str, span in zip(self.string_tab, FIELD_RANGES):
            split_field_str = field_str.split(',')
            if len(split_field_str) > 1 and "*" in split_field_str:
                self._valid = False
                raise ValueError("\"*\" must be alone in a field.")

            unified = set()
            for cron_atom in split_field_str:
                # parse_atom only handles static cases
                for special_char in ('%', '#', 'L', 'W'):
                    if special_char in cron_atom:
                        break
                else:
                    if span == YEARS and field_str == "*" :  # don't create  numerical_tab for all years
                        unified.update(set())
                    else :
                        unified.update(self._parse_atom(cron_atom, span))

            self.numerical_tab.append(unified)
#        print("string_tab : {0}".format(self.string_tab))
#        print("numtab : {0}".format(self.numerical_tab))
        if self.string_tab[2] == "*" and self.string_tab[4] != "*":
            self.numerical_tab[2] = set()

    def get_next_date_special(self, date_tuple, utc_offset=0):
        """
        Returns next ephemeris date the given time.
        The date tuple should be in the local time.
        return date tupple
        """
        cpm = None;
        if self.string_tab == '@fullmoon':
            cpm = ephem.next_full_moon(date_tuple)
        elif self.string_tab == '@newmoon':
            cpm = ephem.next_new_moon(date_tuple)
        elif self.string_tab == '@firstquarter':
            cpm = ephem.next_first_quarter_moon(date_tuple)
        elif self.string_tab == '@lastquarter':
            cpm = ephem.next_last_quarter_moon(date_tuple)
        elif self.string_tab == '@equinox':
            cpm = ephem.next_equinox(date_tuple)
        elif self.string_tab == '@solstice':
            cpm = ephem.next_solstice(date_tuple)
        elif self.string_tab in ['@dawn', '@dusk']:
            bobs = ephem.Sun()
            date = "{0}/{1}/{2}".format(date_tuple[0], date_tuple[1], date_tuple[2])
            if self.string_tab == '@dawn':
                cpm = self._city.next_rising(bobs, start=date)
            else:
                cpm = self._city.next_setting(bobs, start=date)

        if cpm:
            return cpm.tuple()[:-1]
        return None

    def check_trigger_now(self):
        now = datetime.datetime.now()
        return self.check_trigger((now.year, now.month, now.day, now.hour, now.minute))

    def check_trigger(self, date_tuple, utc_offset=0):
        if self._valid == False : return False
        if self._special:
            return self._check_trigger_special(date_tuple, utc_offset)
        else:
            return self._check_trigger_normal(date_tuple, utc_offset)

    def _check_trigger_special(self, date_tuple, utc_offset=0):
        """
        Returns boolean indicating if the trigger is active at the given time.
        The date tuple should be in the local time.
        """
        return date_tuple == self.get_next_date_special(date_tuple, utc_offset)


    def _check_trigger_normal(self, date_tuple, utc_offset=0):
        """
        Returns boolean indicating if the trigger is active at the given time.
        The date tuple should be in the local time. Unless periodicities are
        used, utc_offset does not need to be specified. If periodicities are
        used, specifically in the hour and minutes fields, it is crucial that
        the utc_offset is specified.
        """
        year, month, day, hour, mins = date_tuple
        given_date = datetime.date(year, month, day)
        zeroday = datetime.date(*self.epoch[:3])
        last_dom = calendar.monthrange(year, month)[-1]
        dom_matched = True

        # In calendar and datetime.date.weekday, Monday = 0
        given_dow = (datetime.date.weekday(given_date) + 1) % 7
        first_dow = (given_dow + 1 - day) % 7

        # Figure out how much time has passed from the epoch to the given date
        utc_diff = utc_offset - self.epoch[5]
        mod_delta_yrs = year - self.epoch[0]
        mod_delta_mon = month - self.epoch[1] + mod_delta_yrs * 12
        mod_delta_day = (given_date - zeroday).days
        mod_delta_hrs = hour - self.epoch[3] + mod_delta_day * 24 + utc_diff
        mod_delta_min = mins - self.epoch[4] + mod_delta_hrs * 60

        # Makes iterating through like components easier.
        quintuple = zip(
            (mins, hour, day, month, given_dow, year),
            self.numerical_tab,
            self.string_tab,
            (mod_delta_min, mod_delta_hrs, mod_delta_day, mod_delta_mon, mod_delta_day, mod_delta_yrs),
            FIELD_RANGES)

        for value, valid_values, field_str, delta_t, field_type in quintuple:
            # All valid, static values for the fields are stored in sets
            print(u"Match for {0} value {1} in {2}".format(field_type, value, valid_values))
            if value in valid_values:
                continue

            # The following for loop implements the logic for context
            # sensitive and epoch sensitive constraints. break statements,
            # which are executed when a match is found, lead to a continue
            # in the outer loop. If there are no matches found, the given date
            # does not match expression constraints, so the function returns
            # False as seen at the end of this for...else... construct.
            for cron_atom in field_str.split(','):
                if cron_atom[0] == '%':
                    if not(delta_t % int(cron_atom[1:])):
                        break

                elif field_type == DAYS_OF_WEEK and '#' in cron_atom:
                    D, N = int(cron_atom[0]), int(cron_atom[2])
                    # Computes Nth occurence of D day of the week
                    if (((D - first_dow) % 7) + 1 + 7 * (N - 1)) == day:
                        break

                elif field_type == DAYS_OF_MONTH and cron_atom[-1] == 'W':
                    target = min(int(cron_atom[:-1]), last_dom)
                    lands_on = (first_dow + target - 1) % 7
                    if lands_on == 0:
                        # Shift from Sun. to Mon. unless Mon. is next month
                        target += 1 if target < last_dom else -2
                    elif lands_on == 6:
                        # Shift from Sat. to Fri. unless Fri. in prior month
                        target += -1 if target > 1 else 2

                    # Break if the day is correct, and target is a weekday
                    if target == day and (first_dow + target - 7) % 7 > 1:
                        break

                elif field_type in L_FIELDS and cron_atom.endswith('L'):
                    # In dom field, L means the last day of the month
                    target = last_dom

                    if field_type == DAYS_OF_WEEK:
                        # Calculates the last occurence of given day of week
                        desired_dow = int(cron_atom[:-1])
                        target = (((desired_dow - first_dow) % 7) + 29)
                        target -= 7 if target > last_dom else 0

                    if target == day:
                        break
            else:
                # See 2010.11.15 of CHANGELOG
                if field_type == DAYS_OF_MONTH and self.string_tab[4] != '*':
                    dom_matched = False
                    continue
                elif field_type == DAYS_OF_WEEK and self.string_tab[2] != '*':
                    # If we got here, then days of months validated so it does
                    # not matter that days of the week failed.
                    return dom_matched
                elif field_type == YEARS and self.string_tab[5] == '*':
                    # All years valids
                    continue

                # None of the expressions matched which means this field fails
                return False

        # Arriving at this point means the date landed within the constraints
        # of all fields; the associated trigger should be fired.
        return True


    def _parse_atom(self, parse, minmax):
        """
        Returns a set containing valid values for a given cron-style range of
        numbers. The 'minmax' arguments is a two element iterable containing the
        inclusive upper and lower limits of the expression.

        Examples:
        >>> parse_atom("1-5",(0,6))
        set([1, 2, 3, 4, 5])

        >>> parse_atom("*/6",(0,23))
        set([0, 6, 12, 18])

        >>> parse_atom("18-6/4",(0,23))
        set([18, 22, 0, 4])

        >>> parse_atom("*/9",(0,23))
        set([0, 9, 18])
        """
#        print("CronExpression > _parse_atom. parse = {0}, minmax = {1}".format(parse, minmax))
        try:
            parse = parse.strip()
            increment = 1
            if parse == '*':
                return set(xrange(minmax[0], minmax[1] + 1))
            elif parse.isdigit():
                # A single number still needs to be returned as a set
                value = int(parse)
                if value >= minmax[0] and value <= minmax[1]:
                    return set((value,))
                else:
                    self._valid = False
                    raise ValueError("Invalid bounds: \"{0}\"".format(parse))
            elif '-' in parse or '/' in parse:
                divide = parse.split('/')
                subrange = divide[0]
                if len(divide) == 2:
                    # Example: 1-3/5 or */7 increment should be 5 and 7 respectively
                    increment = int(divide[1])

                if '-' in subrange:
                    # Example: a-b
                    prefix, suffix = [int(n) for n in subrange.split('-')]
                    if prefix < minmax[0] or suffix > minmax[1]:
                        self._valid = False
                        raise ValueError("Invalid bounds: \"{0}\"".format(parse))
                elif subrange == '*':
                    # Include all values with the given range
                    prefix, suffix = minmax[0], minmax[1]
                else:
                    try :
                        prefix = int(subrange)
                        suffix = prefix
                    except :
                        self._valid = False
                        raise ValueError("Unrecognized symbol: \"{0}\"".format(subrange))

                if prefix < suffix:
                    # Example: 7-10
                    return set(xrange(prefix, suffix + 1, increment))
                else:
                    # Example: 12-4/2; (12, 12 + n, ..., 12 + m*n) U (n_0, ..., 4)
                    noskips = list(xrange(prefix, minmax[1] + 1))
                    noskips+= list(xrange(minmax[0], suffix + 1))
                    return set(noskips[::increment])
        except:
            # TODO : handle the error in a better way !
            # it happens for example when a bad cron expression is set (month = 0 instead of 1-12 for example)
            print("ERROR : bad value : {0}. Expected : {1}. Error : {2}".format(parse, minmax, traceback.format_exc()))
            return []  # we return an empty set as the expression is invalid

if __name__ == "__main__":
    job = CronExpression("@fullmoon")
    print(job)
    print(job.check_trigger_now())
    print(job.check_trigger((2016, 12, 14, 0, 5)))
    print(job.get_next_date_special((2016, 12, 16, 0, 5)))
    print("")
    job = CronExpression("@dawn")
    print(job)
    print(job.check_trigger_now())
    print(job.check_trigger((2016, 12, 7, 7, 26)))
    print(job.get_next_date_special((2016, 12, 16, 0, 5)))
    print("")
    job = CronExpression("@dusk")
    print(job)
    print(job.check_trigger_now())
    print(job.check_trigger((2016, 12, 7, 7, 26)))
    print("")
    job = CronExpression("@equinox")
    print(job._city)
    print(job)
    print(job.check_trigger_now())
    print("")
    job = CronExpression("@solstice")
    print(job._city)
    print(job)
    print(job.check_trigger_now())
    print(job.check_trigger((2016, 12, 21, 10, 44)))
    print(job.get_next_date_special((2016, 12, 22, 0, 5)))
    print("")
    #print(job.check_trigger((2010, 11, 17, 0, 0)))
    job = CronExpression("0 0 * * 1-5/2 find /var/log -delete")
    print(job)
    print(job.check_trigger_now())
    print(job.check_trigger((2010, 11, 17, 0, 0)))
    print(job.check_trigger((2012, 12, 21, 0 , 0)))
    print("")
    job = CronExpression("@midnight Feed 'it'", (2010, 5, 1, 7, 0, -6))
    print(job)
    print(job.check_trigger((2010, 5, 1, 7, 0), utc_offset=-6))
    print(job.check_trigger((2010, 5, 1, 16, 0), utc_offset=-6))
    print(job.check_trigger((2010, 5, 2, 1, 0), utc_offset=-6))
    print("")
    print(ephem.cities.lookup("paris, france"))
    print("**************************************************")
    job = CronExpression(("5-10 10,16 ? 2/3 1#2 2017/100"))
    print("cron valid : {0}".format(job.isValidate()))
    print(job.check_trigger((2017, 2, 13, 10 , 6)))
    print("")
    job = CronExpression(("10 12-15 ? 1-6 5 205"))
    print("cron valid : {0}".format(job.isValidate()))
    print(job.check_trigger((2017, 2, 13, 10 , 6)))
    print("")
    job = CronExpression(("*/10 */2 * * *"))
    print("cron valid : {0}".format(job.isValidate()))
    print(job.check_trigger((2017, 2, 13, 10 , 20)))
    print("")
