#!/usr/bin/python3
import flask
import psycopg2
import Doorbot.Config
import Doorbot.DB
from Doorbot.API import app

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
    'host=' + host,
    'port=' + str( port ),
])
conn = psycopg2.connect( conn_str )
Doorbot.DB.set_db( conn )

if __name__ == "__main__":
    app.run( host = "0.0.0.0" )
