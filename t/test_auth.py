import unittest
import psycopg2
import os
import re
import sqlite3
import Doorbot.Config
import Doorbot.SQLAlchemy
from sqlalchemy import select
from sqlalchemy.orm import Session


RFID = "1234"
ROLE_NAME = "doors"


class TestAuth( unittest.TestCase ):
    @classmethod
    def setUpClass( cls ):
        if 'PG' != os.environ.get( 'DB' ):
            Doorbot.SQLAlchemy.set_engine_sqlite()

        global engine
        engine = Doorbot.SQLAlchemy.get_engine()

        permission_back_door = Doorbot.SQLAlchemy.Permission(
            name = "back.door",
        )
        permission_front_door = Doorbot.SQLAlchemy.Permission(
            name = "front.door",
        )
        permission_other_thing = Doorbot.SQLAlchemy.Permission(
            name = "other.thing",
        )

        role_doors = Doorbot.SQLAlchemy.Role(
            name = ROLE_NAME,
        )
        role_doors.permissions.append( permission_back_door )
        role_doors.permissions.append( permission_front_door )

        member = Doorbot.SQLAlchemy.Member(
            full_name = "_tester",
            rfid = RFID,
        )
        member.roles.append( role_doors )

        session = Session( engine )
        session.add_all([
            permission_back_door,
            permission_front_door,
            permission_other_thing,
            role_doors,
            member,
        ])
        session.commit()

    def test_role_has_permission( self ):
        session = Session( engine )

        role_fetch_stmt = select( Doorbot.SQLAlchemy.Role ).where(
            Doorbot.SQLAlchemy.Role.name == ROLE_NAME
        )
        role = session.scalars( role_fetch_stmt ).one()

        self.assertTrue( role.has_permission( "back.door" ),
            "Role has back.door permission" )
        self.assertTrue( role.has_permission( "front.door" ),
            "Role has front.door permission" )
        self.assertFalse( role.has_permission( "other.thing" ),
            "Role does not have other.thing permission" )

    def test_member_has_permission( self ):
        session = Session( engine )

        member_fetch_stmt = select( Doorbot.SQLAlchemy.Member ).where(
            Doorbot.SQLAlchemy.Member.rfid == RFID
        )
        member = session.scalars( member_fetch_stmt ).one()

        self.assertTrue( member.has_permission( "back.door" ),
            "Member has back.door permission via role" )
        self.assertTrue( member.has_permission( "front.door" ),
            "Member has front.door permission via role" )
        self.assertFalse( member.has_permission( "other.thing" ),
            "Member does not have other.thing permission" )
