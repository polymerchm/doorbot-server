#!/usr/bin/python3
import flask
import psycopg2
import Doorbot.Config
import Doorbot.Pages
import Doorbot.SQLAlchemy
from Doorbot.API import app
from datetime import timedelta


session_conf = Doorbot.Config.get( 'session' )
app.secret_key = session_conf[ 'key' ]
app.config[ 'PERMANENT_SESSION_LIFETIME' ] = timedelta(
    minutes = session_conf[ 'life_minutes' ]
)
