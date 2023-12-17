import unittest
import flask_unittest
import flask.globals
from flask import json
import os
import psycopg2
import re
import sqlite3
import Doorbot.Config
import Doorbot.API
import Doorbot.SQLAlchemy
from sqlalchemy import select
from sqlalchemy.orm import Session


USER_PASS = ( "user", "pass" )

class TestAPIChangePassword( flask_unittest.ClientTestCase ):
    app = Doorbot.API.app
    engine = None

    @classmethod
    def setUpClass( cls ):
        if 'PG' != os.environ.get( 'DB' ):
            Doorbot.SQLAlchemy.set_engine_sqlite()

        global engine
        engine = Doorbot.SQLAlchemy.get_engine()

        member = Doorbot.SQLAlchemy.Member(
            full_name = "_tester",
            rfid = USER_PASS[0],
        )
        member.set_password( USER_PASS[1], {
            "type": "plaintext",
        })

        session = Session( engine )
        session.add( member )
        session.commit()

    def test_change_password( self, client ):
        session = Session( engine )
        stmt = select( Doorbot.SQLAlchemy.Member ).where(
            Doorbot.SQLAlchemy.Member.rfid == USER_PASS[0]
        )
        member = session.scalars( stmt ).one()

        assert( member.check_password( USER_PASS[1] ), "Old password works" )

        rv = client.put( '/secure/change_passwd/' + USER_PASS[0], data = {
            "new_pass": USER_PASS[1] + "foo",
            "new_pass2": USER_PASS[1] + "foo",
        })
        self.assertStatus( rv, 200 )

        assert( not member.check_password( USER_PASS[1] ),
            "Old password no longer works" )
        assert( member.check_password( USER_PASS[1] + "foo" ),
            "New password works" )
