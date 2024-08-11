import json
import sys
from Doorbot.SQLAlchemy import Member
from Doorbot.SQLAlchemy import get_session
from sqlalchemy import update


session = get_session()

wrong_name_members = json.load( sys.stdin )

for member in wrong_name_members:
    print( f"Changing {member['rfid']} from '{member['name_db']}' to '{member['name_mms']}'" )
    stmt = update( Member ).where(Member.rfid == member[ 'rfid']).values(full_name = member[ 'name_mms'])
    session.execute(stmt)
session.commit()
session.close()
