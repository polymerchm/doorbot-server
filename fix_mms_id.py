import json
import sys
import Doorbot.Config
import Doorbot.DB as DB
import psycopg2

UPDATE_MMS_ID = 'UPDATE members SET mms_id = %s WHERE rfid = %s'


db = DB.db_connect()

members = json.load( sys.stdin )

for member in members:
    rfid = member[ 'rfid' ]
    mms_id = member[ 'mms_id' ]
    print( f"Setting {rfid} ('{member['name_db']}') to '{mms_id}'" )
    cur = db.cursor()
    cur.execute( UPDATE_MMS_ID, ( mms_id, rfid ) )
    cur.close()
