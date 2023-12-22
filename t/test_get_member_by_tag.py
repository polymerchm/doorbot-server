import unittest
import psycopg2
import os
import re
import sqlite3
import Doorbot.Config
import Doorbot.SQLAlchemy
from sqlalchemy import select
from sqlalchemy.orm import Session


RFID_FOO = "1234"
FULL_NAME = "foo"

class TestGetMemberByTag( unittest.TestCase ):
    @classmethod
    def setUpClass( cls ):
        if 'PG' != os.environ.get( 'DB' ):
            Doorbot.SQLAlchemy.set_engine_sqlite()

        global engine
        engine = Doorbot.SQLAlchemy.get_engine()

        member_foo = Doorbot.SQLAlchemy.Member(
            full_name = FULL_NAME,
            rfid = RFID_FOO,
        )

        session = Session( engine )
        session.add( member_foo )
        session.commit()

    def test_get_member_by_tag( self ):
        session = Session( engine )
        member = Doorbot.SQLAlchemy.Member.get_by_tag( RFID_FOO, session )

        assert member.full_name == FULL_NAME, "Fetched correct member"
