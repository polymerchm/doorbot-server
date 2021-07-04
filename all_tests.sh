#!/bin/bash
TEST=$1
cd t
PYTHONPATH=../:${PYTHONPATH} python3 -m nose2 ${TEST}
