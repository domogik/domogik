Rivescript informations
=======================

The included rivescript library is version 1.0.6 : https://github.com/aichaos/rivescript-python/archive/v1.06.zip

Patches applied on rivescript/python.py
=======================================

    30d29
    < 
    88c87,92
    <         return str(reply)
    ---
    >         ### Fritz - patch
    >         # old #
    >         #return str(reply)
    >         # new #
    >         return reply
    >         ### Fritz - patch end

Patches applied on the library
==============================

The library is patched :


    85a86,94
    > ### Fritz - patch
    > # old #
    > # (nothing) #
    > # new #
    > import unicodedata
    > 
    > DEFAULT_WEIGHT = 10
    > print("/!\ Rivescript 1.80, patched for Domogik purpose")
    > ### Fritz - patch end
    1112c1121,1126
    <             0: []  # Default priority=0
    ---
    >             ### fritz - patch
    >             # old #
    >             # 0: []  # Default priority=0
    >             # new #
    >             DEFAULT_WEIGHT: []  # Default priority
    >             ### fritz - patch end
    1116c1130,1135
    <             match, weight = re.search(RE.weight, trig), 0
    ---
    >             # fritz - patch
    >             # old #
    >             # match, weight = re.search(RE.weight, trig), 0
    >             # new #
    >             match, weight = re.search(RE.weight, trig), DEFAULT_WEIGHT
    >             # fritz - patch end
    1590a1610,1614
    > 
    >             # fritz patch
    >             # replace accented by non accented characters for latin languages
    >             msg = remove_accents(msg) 
    >             # fritz patch end
    1830c1854,1859
    <                     weight = 1
    ---
    >                     ### fritz - patch
    >                     # old #
    >                     # weight = 1
    >                     # new #
    >                     weight = DEFAULT_WEIGHT
    >                     ### fritz - patch end
    2503a2533,2540
    > # fritz patch
    > # old #
    > # (nothing)
    > # new #
    > def remove_accents(input_str):
    >     nfkd_form = unicodedata.normalize('NFKD', input_str)
    >     return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    > # fritz patch end

This is needed to allow some brain packages to propose some actions with some generic sentences that could also be used in other brain packages which are more important.
For example, the wolfram package should be used only when there is no other match.
As the default weight with rivescript is set to 1, this is not possible. Thanks to the patch, that set the default weight to 10, it is possible to make some brain packages not important.

