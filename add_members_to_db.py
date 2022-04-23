import json
import Doorbot.Config
import Doorbot.DB as DB
import psycopg2
import sys


db = DB.db_connect()
DB.set_db( db )
members = json.load( sys.stdin )


for member in members:
    mms_id = member[ 'mms_id' ]
    display_name = member[ 'name_mms' ]
    rfid = member[ 'rfid' ]
    print( f"Adding {rfid} as '{display_name}', mms_id '{mms_id}'" )
    DB.add_member(
        display_name,
        rfid,
        mms_id,
    )
