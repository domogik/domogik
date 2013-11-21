#!/bin/bash

# unittests
python $TRAVIS_BUILD_DIR/src/domogik/tests/unittests/scenario_parameters.py
python $TRAVIS_BUILD_DIR/src/domogik/tests/unittests/xplmessage_test.py

# testcases for domogik
python $TRAVIS_BUILD_DIR/src/domogik/tests/domogik_testcase.py
ps -U $LOGNAME 
ps -U root 
