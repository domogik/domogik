#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

ln -s $TRAVIS_BUILD_DIR /var/lib/domogik/domogik_packages/plugin_$DMG_PLUGIN
ls -l /var/lib/domogik/domogik_packages/plugin_$DMG_PLUGIN/
