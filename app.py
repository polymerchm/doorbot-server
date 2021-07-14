import flask
import psycopg2
import Doorbot.Config
import Doorbot.DB
from Doorbot.API import app

if __name__ == "__main__":
    pg_conf = Doorbot.Config.get( 'postgresql' )
    user = pg_conf[ 'username' ]
    passwd = pg_conf[ 'passwd' ]
    database = pg_conf[ 'database' ]

    conn_str = ' '.join([
        'dbname=' + database,
        'user=' + user,
        'password=' + passwd,
    ])
    conn = psycopg2.connect( conn_str )
    Doorbot.DB.set_db( conn )
