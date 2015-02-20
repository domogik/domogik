#!/bin/bash -e
echo "=== Start virtualenv dmg_==="
source /home/travis/virtualenv/python2.7/bin/activate

echo "=== Install the plugin ==="
dmg_package -i https://github.com/domogik/domogik-plugin-test/archive/master.zip

echo "=== Run the plugin testcases ==="
dmg_testrunner --allow-alter /var/lib/domogik/domogik_packages/plugin_test/tests
if [[ $rc != 0 ]]; then exit $rc; fi

echo "=== Uninstall the plugin ==="
dmg_package -r plugin_test
