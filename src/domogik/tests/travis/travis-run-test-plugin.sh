#!/bin/bash -e
echo "=== Install the plugin ==="
sudo /usr/local/bin/dmg_package -i https://github.com/domogik/domogik-plugin-test/archive/master.zip
ls /var/lib/domogik/domogik_packages

echo "=== Run the plugin testcases ==="
sudo src/domogik/tests/bin/testrunner.py /var/lib/domogik/domogik_packages/plugin_test/tests

echo "=== Uninstall the plugin ==="
sudo /usr/local/bin/dmg_package -r plugin_test
