import json
import sys
from Doorbot.SQLAlchemy import Member
from Doorbot.SQLAlchemy import get_session
from sqlalchemy import update

session = get_session()

members = json.load( sys.stdin )


for member in members:
    rfid = member[ 'rfid' ]
    print( f"Member {rfid} is {member['is_active_mms']} in MMS, but {member['is_active_db']} in DB; setting DB to MMS" )
    
    stmt = update( Member ).where(Member.rfid == rfid).values(active = member[ 'is_active_mms' ])
    session.execute(stmt)
session.commit()
session.close()    

