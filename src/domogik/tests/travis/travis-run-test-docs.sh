#!/bin/bash -e

echo "=== Build the sphinx docs ==="
cd $TRAVIS_BUILD_DIR/docs
make html
cd -

