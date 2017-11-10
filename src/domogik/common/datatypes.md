About the datatypes.json file
=============================

This file contains the description of all the available datatypes in a Domogik release.

Each sensor or command of a device is related to a datatype. Some of them are very similar and so, are grouped as childs/parents.

Particular use cases
====================

Color related datatypes
-----------------------

The color related datatypes don't have the same parent because their basic format is different :

* DT_ColorRGBHexa is a hexadecimal view of a color. Basically, this is a string. Example for red : FF0000
* DT_ColorRGB is a list of 3 values for rd, green and blue from 0 to 255.. Example for red : 255, 0, 0

On the user interfaces, the way to interact with a sensor is related to its datatype and to avoir too much useless code, in 90% of the cases, it is related to the parent datatype.

This is why there is no DT_Color parent datatype.
