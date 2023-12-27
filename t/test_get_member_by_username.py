import unittest
import psycopg2
import os
import re
import sqlite3
import Doorbot.Config
import Doorbot.SQLAlchemy
from sqlalchemy import select
from sqlalchemy.orm import Session


USERNAME = "foo"
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
            rfid = "1234",
            username = USERNAME,
        )

        session = Session( engine )
        session.add( member_foo )
        session.commit()

    def test_get_member_by_username( self ):
        session = Session( engine )
        member = Doorbot.SQLAlchemy.Member.get_by_username( USERNAME, session )

        assert member.full_name == FULL_NAME, "Fetched correct member"
