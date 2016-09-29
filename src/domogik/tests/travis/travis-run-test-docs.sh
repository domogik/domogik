#!/bin/bash -e
echo "=== Build the sphinx docs ==="
cd docs
make html
cd ../
