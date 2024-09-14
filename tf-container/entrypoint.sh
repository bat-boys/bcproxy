#!/bin/bash

/usr/local/bin/bcproxy -4 2901 &
/usr/local/bin/tf -f/usr/local/share/tf-lib/py/tfrc -n
