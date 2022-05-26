#!/usr/bin/python3
import flask
import psycopg2
import Doorbot.Config
import Doorbot.DB
from Doorbot.API import app

conn = Doorbot.DB.db_connect()
Doorbot.DB.set_db( conn )

if __name__ == "__main__":
    app.run( host = "0.0.0.0" )
