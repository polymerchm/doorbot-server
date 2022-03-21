import json
import sys

got = json.load( sys.stdin )
want = got[ 'clear_members' ]
json.dump( want, sys.stdout )
