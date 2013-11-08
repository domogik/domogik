#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

ln -s $(pwd) /var/lib/domogik/domogik_packages/plugin_$1
