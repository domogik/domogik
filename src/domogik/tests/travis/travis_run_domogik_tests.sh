#!/bin/bash

# unittests
python $TRAVIS_BUILD_DIR/src/domogik/tests/unittests/scenario_parameters.py
python $TRAVIS_BUILD_DIR/src/domogik/tests/unittests/xplmessage_test.py

echo "ps aux | grep domo"
ps aux | grep domo
echo "ps aux | grep dmg"
ps aux | grep dmg
echo "ps aux | grep rest"
echo "ps aux | grep dbmgr"
echo "ps aux | grep xplgw"
echo "ps u -U $LOGNAME"
ps u -U $LOGNAME

# testcases for domogik
python $TRAVIS_BUILD_DIR/src/domogik/tests/domogik_testcase.py
