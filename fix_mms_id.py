import json
import sys
from Doorbot.SQLAlchemy import Member
from Doorbot.SQLAlchemy import get_session
from sqlalchemy import update

session = get_session()
members = json.load( sys.stdin )

for member in members:
    rfid = member[ 'rfid' ]
    mms_id = member[ 'mms_id' ]
    stmt = update ( Member ).where(Member.rfid == rfid).values(mms_id = mms_id)
    print( f"Setting {rfid} ('{member['name_db']}') to '{mms_id}'" )
    session.execute( stmt )
session.commit()
session.close()
