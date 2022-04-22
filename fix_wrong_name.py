import json
import sys
import Doorbot.Config
import Doorbot.DB as DB
import psycopg2


db = DB.db_connect()
DB.set_db( db )

wrong_name_members = json.load( sys.stdin )

for member in wrong_name_members:
    print( f"Changing {member['rfid']} from '{member['name_db']}' to '{member['name_mms']}'" )
    DB.change_name(
        member[ 'rfid' ],
        member[ 'name_mms' ],
    )
