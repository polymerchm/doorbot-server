#!/usr/bin/python3
import flask
import psycopg2
import Doorbot.Config
import Doorbot.SQLAlchemy
from Doorbot.API import app


if __name__ == "__main__":
    app.run( host = "0.0.0.0" )
