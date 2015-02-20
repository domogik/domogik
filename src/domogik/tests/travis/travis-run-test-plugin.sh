echo "=== Install the plugin ==="
sudo dmg_package -i https://github.com/domogik/domogik-plugin-test/archive/master.zip

echo "=== Run the plugin testcases ==="
sudo src/domogik/tests/bin/testrunner.py /var/lib/domogik/domogik_packages/plugin_test/tests
ls /var/lib/domogik/domogik_packages

echo "=== Uninstall the plugin ==="
sudo dmg_package -r plugin_test
