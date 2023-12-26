#!/usr/bin/python3
import flask
import psycopg2
import Doorbot.Config
import Doorbot.SQLAlchemy
from Doorbot.API import app


session_conf = Doorbot.Config.get( 'session' )
app.secret_key = session_conf[ 'key' ]
app.config[ 'PERMANENT_SESSION_LIFETIME' ] = timedelta(
    minutes = session_conf[ 'life_minutes' ]
)

if __name__ == "__main__":
    app.run( host = "0.0.0.0" )
