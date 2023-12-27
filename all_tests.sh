#!/bin/bash
TEST=$1
FLASK_APP=app
cd t
PYTHONPATH=./:../:${PYTHONPATH} coverage run --source .,../Doorbot -m nose2 ${TEST}

coverage report
