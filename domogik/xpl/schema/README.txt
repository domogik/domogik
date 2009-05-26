# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author : Marc Schneider <marc@domogik.org>

# $LastChangedBy: maxence $
# $LastChangedDate: 2009-02-20 20:39:25 +0100 (ven 20 fév 2009) $
# $LastChangedRevision: 382 $

xPL is a message-based distributed system. It allows process to cummunicate using
simple text messages. Message specification is defined by schemas. Lot of schemas 
are already defined by the xPL Project [1].
Anyway, Domogik needs some functionnality which are *not* described in any schema.
This directory contains schema definitions. Each schema is decribed as in the xPL projet.

## Template :
<Class>.<type> Message Specification

    * Class = <Class>
    * Type = <type>

This schema provides basic information relating to <short description>

=== XPL-TRIG Structure ===
<Class>.<Type>
{
KEY1=<value format or description>
KEY2=<value format or description>
[OPTIONAL_KEY3=<value format or description>]
}
=== XPL-CMND Structure ===

<Class>.<Type>
{
KEY1=<value format or description>
KEY2=<value format or description>
[OPTIONAL_KEY3=<value format or description>]
}

=== XPL-STAT Structure ===


HBEAT.*
{
(hbeat items)
}

or

<Class>.<Type>
{
KEY1=<value format or description>
KEY2=<value format or description>
[OPTIONAL_KEY3=<value format or description>]
}

Schema Specific Notes 
<What you want>
