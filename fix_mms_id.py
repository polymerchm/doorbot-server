import json
import sys
import Doorbot.Config
from Doorbot.SQLAlchemy import Location
from Doorbot.SQLAlchemy import EntryLog
from Doorbot.SQLAlchemy import Member
from Doorbot.SQLAlchemy import Permission
from Doorbot.SQLAlchemy import Role
from Doorbot.SQLAlchemy import get_engine
from Doorbot.SQLAlchemy import get_session
from datetime import datetime
from flask_httpauth import HTTPBasicAuth
from sqlalchemy import select
from sqlalchemy.sql import text
import psycopg2

UPDATE_MMS_ID = 'UPDATE members SET mms_id = %s WHERE rfid = %s'


db =get_engine().connect()

members = json.load( sys.stdin )

for member in members:
    rfid = member[ 'rfid' ]
    mms_id = member[ 'mms_id' ]
    print( f"Setting {rfid} ('{member['name_db']}') to '{mms_id}'" )
    cur = db.cursor()
    cur.execute( UPDATE_MMS_ID, ( mms_id, rfid ) )
    cur.close()
