#!/bin/bash -e
echo "=== Start virtualenv ==="
source /home/travis/virtualenv/python2.7/bin/activate

echo "=== Install the plugin ==="
dmg_package -i https://github.com/domogik/domogik-plugin-test/archive/master.zip
ls /var/lib/domogik/domogik_packages

echo "=== Run the plugin testcases ==="
src/domogik/tests/bin/testrunner.py /var/lib/domogik/domogik_packages/plugin_test/tests

echo "=== Uninstall the plugin ==="
dmg_package -r plugin_test
