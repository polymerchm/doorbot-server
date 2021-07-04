#!/bin/bash
TEST=$1
FLASK_APP=app
cd t
PYTHONPATH=./:../:${PYTHONPATH} python3 -m nose2 ${TEST}
