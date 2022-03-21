import argparse
import json
import sys

parser = argparse.ArgumentParser(
    description = 'Filter members by types'
)
parser.add_argument(
    '--clear',
    action = 'store_true',
    help = 'Members that match between the MMS and DB',
)
parser.add_argument(
    '--zerod',
    action = 'store_true',
    help = 'Members that have zero\'d out RFID keys in the MMS',
)
parser.add_argument(
    '--wrong-name',
    action = 'store_true',
    help = 'Members with a different name between the MMS and DB',
)
parser.add_argument(
    '--wrong-active',
    action = 'store_true',
    help = 'Members with a different active status between the MMS and DB',
)
parser.add_argument(
    '--add-to-db',
    action = 'store_true',
    help = 'Members that appear in the MMS, but not the DB',
)
parser.add_argument(
    '--add-to-mms',
    action = 'store_true',
    help = 'Members that appare in the DB, but not the MMS',
)
parser.add_argument(
    '--no-mms-id',
    action = 'store_true',
    help = 'Members with no MMS ID listed in the DB',
)
args = vars( parser.parse_args() )


got = json.load( sys.stdin )
global want
want = []
if args[ 'clear' ]:
    want = got[ 'clear_members' ]
if args[ 'zerod' ]:
    want = got[ 'zerod_members' ]
if args[ 'wrong_name' ]:
    want = got[ 'wrong_name_members' ]
if args[ 'wrong_active' ]:
    want = got[ 'wrong_active_members' ]
if args[ 'add_to_db' ]:
    want = got[ 'add_to_db_members' ]
if args[ 'add_to_mms' ]:
    want = got[ 'add_to_mms_members' ]
if args[ 'no_mms_id' ]:
    want = got[ 'no_mms_id_in_db_members' ]

json.dump( want, sys.stdout )
