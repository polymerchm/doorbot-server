import json
import Doorbot.Config
import Doorbot.DB as DB
import psycopg2
import sys


db = DB.db_connect()
DB.set_db( db )
members = json.load( sys.stdin )


for member in members:
    mms = member[ 'mms' ]
    print( f"Adding {mms['rfid']} as '{mms['display_name']}', mms_id '{mms['id']}' active: {mms['is_active_tag']}" )
    #DB.add_member(
    #    mms['display_name'],
    #    mms['rfid'],
    #    mms['id'],
    #)
