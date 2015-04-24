Rivescript informations
=======================

The included rivescript library is version 1.0.6 : https://github.com/aichaos/rivescript-python/archive/v1.06.zip

Patches applied on the library
==============================

The library is patched :

    53,57d52
    < ### Patch for Domogik
    < DEFAULT_WEIGHT = 10
    < print("/!\ Rivescript 1.06, patched for Domogik")
    < ### End of patch
    < 
    1052,1055c1047
    <             ### Patch for Domogik : change default weight
    <             # 0: []  # Default priority=0
    <             DEFAULT_WEIGHT: []  # Default priority
    <             ### End of patch
    ---
    >             0: []  # Default priority=0
    1059,1062c1051
    <             ### Patch for Domogik : change default weight
    <             # match, weight = re.search(re_weight, trig), 0
    <             match, weight = re.search(re_weight, trig), 10
    <             ### End of patch
    ---
    >             match, weight = re.search(re_weight, trig), 0
    1763,1766c1752
    <                     ### Patch for Domogik : change default weight
    <                     #weight = 1
    <                     weight = DEFAULT_WEIGHT
    <                     ### End of patch
    ---
    >                     weight = 1


This is needed to allow some brain packages to propose some actions with some generic sentences that could also be used in other brain packages which are more important.
For example, the wolfram package should be used only when there is no other match.
As the default weight with rivescript is set to 1, this is not possible. Thanks to the patch, that set the default weight to 10, it is possible to make some brain packages not important.

