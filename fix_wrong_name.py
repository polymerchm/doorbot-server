import json
import sys
import Doorbot.Config
import Doorbot.DB as DB
import psycopg2

def db_connect():
    pg_conf = Doorbot.Config.get( 'postgresql' )
    user = pg_conf[ 'username' ]
    passwd = pg_conf[ 'passwd' ]
    database = pg_conf[ 'database' ]
    host = pg_conf[ 'host' ]
    port = pg_conf[ 'port' ]

    conn_str = ' '.join([
        'dbname=' + database,
        'user=' + user,
        'password=' + passwd,
        #'host=' + host,
        #'port=' + str( port ),
    ])

    conn = psycopg2.connect( conn_str )
    conn.set_session( autocommit = True )
    return conn



db = db_connect()
DB.set_db( db )

wrong_name_members = json.load( sys.stdin )

for member in wrong_name_members:
    print( f"Changing {member['rfid']} from '{member['name_db']}' to '{member['name_mms']}'" )
    DB.change_name(
        member[ 'rfid' ],
        member[ 'name_mms' ],
    )
