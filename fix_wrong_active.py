import json
import Doorbot.Config
import Doorbot.DB as DB
import psycopg2
import sys


db = DB.db_connect()
DB.set_db( db )
members = json.load( sys.stdin )


for member in members:
    rfid = member[ 'rfid' ]
    print( f"Member {rfid} is {member['is_active_mms']} in MMS, but {member['is_active_db']} in DB; setting DB to MMS" )
    if member[ 'is_active_mms' ]:
        DB.activate_member( rfid )
    else:
        DB.deactivate_member( rfid )
