import unittest
import psycopg2
import os
import re
import sqlite3
import Doorbot.Config
import Doorbot.SQLAlchemy
from sqlalchemy.orm import Session


USER_PASS = ( "1234", "pass" )
USER2 = "2345"

KNOWN_PASS = "foobar123"
APACHE_MD5_KNOWN_SALT = "123/abCD"
APACHE_MD5_KNOWN_PASS = "$apr1$123/abCD$qVXnv7ltJwsWk3Y9JhLA1/"


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

        self.assertTrue( member.check_password( USER_PASS[1] ),
            "Password is still correct after reencoding" )

    def test_apache_md5_pass( self ):
        member = Doorbot.SQLAlchemy.Member(
            full_name = "_tester",
            rfid = USER2,
            password_type = Doorbot.SQLAlchemy.PASSWORD_TYPE_APACHE_MD5,
            encoded_password = APACHE_MD5_KNOWN_PASS,
        )

        session = Session( engine )
        session.add( member )
        session.commit()

        assert member.check_password( KNOWN_PASS ), "Password checks out w/apache md5"

        assert Doorbot.SQLAlchemy.PASSWORD_TYPE_APACHE_MD5 != member.password_type, "Password encodig type changed after checking it"
