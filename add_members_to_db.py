import json
import sys
from Doorbot.SQLAlchemy import Member
from Doorbot.SQLAlchemy import get_session

session = get_session()
members = json.load( sys.stdin )


for member in members:
    mms_id = member[ 'mms_id' ]
    display_name = member[ 'name_mms' ]
    rfid = member[ 'rfid' ]
    print( f"Adding {rfid} as '{display_name}', mms_id '{mms_id}'" )
    entry = Member(full_name = display_name, rfid = rfid, mms_id = mms_id)
    session.add(entry)
    
session.commit()
session.close()

