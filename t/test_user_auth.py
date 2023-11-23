import unittest
import psycopg2
import os
import re
import sqlite3
import Doorbot.Config
import Doorbot.SQLAlchemy
from sqlalchemy.orm import Session


USER_PASS = ( "1234", "pass" )

class TestAuth( unittest.TestCase ):
    @classmethod
    def setUpClass( cls ):
        if 'PG' != os.environ.get( 'DB' ):
            Doorbot.SQLAlchemy.set_engine_sqlite()

        global engine
        engine = Doorbot.SQLAlchemy.get_engine()

        location = Doorbot.SQLAlchemy.Location(
            name = "cleanroom.door",
        )

        session = Session( engine )
        session.add_all([ location ])
        session.commit()

    def test_add_member( self ):
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

        self.assertFalse( member.check_password( USER_PASS[1] + "foo" ),
            "Bad password is incorrect" )
        self.assertTrue(
            member.password_type == Doorbot.SQLAlchemy.PASSWORD_TYPE_PLAINTEXT,
            "Password encryption type is unchanged with bad password"
        )

        self.assertTrue( member.check_password( USER_PASS[1] ),
            "Password is correct" )
        self.assertTrue(
            member.password_type != Doorbot.SQLAlchemy.PASSWORD_TYPE_PLAINTEXT,
            "Password encryption type was changed after checking password" 
        )
