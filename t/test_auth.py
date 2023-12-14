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
RFID_BAR = "2345"
RFID_BAZ = "3456"


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
        permission_wood_bandsaw = Doorbot.SQLAlchemy.Permission(
            name = "woodshop.bandsaw",
        )
        permission_wood_tablesaw = Doorbot.SQLAlchemy.Permission(
            name = "woodshop.tablesaw",
        )

        role_doors = Doorbot.SQLAlchemy.Role(
            name = "doors",
        )
        role_doors.permissions.append( permission_back_door )
        role_doors.permissions.append( permission_front_door )

        role_wood = Doorbot.SQLAlchemy.Role(
            name = "woodshop",
        )
        role_wood.permissions.append( permission_wood_bandsaw )
        role_wood.permissions.append( permission_wood_tablesaw )

        member_foo = Doorbot.SQLAlchemy.Member(
            full_name = "foo",
            rfid = RFID_FOO,
        )
        member_foo.roles.append( role_doors )

        member_bar = Doorbot.SQLAlchemy.Member(
            full_name = "bar",
            rfid = RFID_BAR,
        )
        member_bar.roles.append( role_wood )

        member_baz = Doorbot.SQLAlchemy.Member(
            full_name = "baz",
            rfid = RFID_BAZ,
        )
        member_baz.roles.append( role_wood )
        member_baz.roles.append( role_doors )

        session = Session( engine )
        session.add_all([
            permission_back_door,
            permission_front_door,
            permission_wood_bandsaw,
            permission_wood_tablesaw,
            role_doors,
            role_wood,
            member_foo,
            member_bar,
            member_baz,
        ])
        session.commit()

    def test_role_has_permission( self ):
        session = Session( engine )

        role_fetch_stmt = select( Doorbot.SQLAlchemy.Role ).where(
            Doorbot.SQLAlchemy.Role.name == "doors"
        )
        role = session.scalars( role_fetch_stmt ).one()

        self.assertTrue( role.has_permission( "back.door" ),
            "Role has back.door permission" )
        self.assertTrue( role.has_permission( "front.door" ),
            "Role has front.door permission" )
        self.assertFalse( role.has_permission( "woodshop.bandsaw" ),
            "Role does not have woodshop.bandsaw permission" )

    def test_member_has_permission( self ):
        session = Session( engine )

        member_fetch_stmt = select( Doorbot.SQLAlchemy.Member ).where(
            Doorbot.SQLAlchemy.Member.rfid == RFID_FOO
        )
        member = session.scalars( member_fetch_stmt ).one()

        self.assertTrue( member.has_permission( "back.door" ),
            "Member has back.door permission via role" )
        self.assertTrue( member.has_permission( "front.door" ),
            "Member has front.door permission via role" )
        self.assertFalse( member.has_permission( "woodshop.bandsaw" ),
            "Member does not have woodshop.bandsaw permission" )

    def test_member_all_roles( self ):
        session = Session( engine )

        member_fetch_stmt = select( Doorbot.SQLAlchemy.Member ).where(
            Doorbot.SQLAlchemy.Member.rfid == RFID_BAZ
        )
        member = session.scalars( member_fetch_stmt ).one()
        roles = member.all_roles()
        role_names = [ x.name for x in roles ]
        role_names.sort()

        self.assertEqual( role_names, [
            "doors",
            "woodshop",
        ], "Roles found as expected" );

    def test_member_all_permissions( self ):
        session = Session( engine )

        member_fetch_stmt = select( Doorbot.SQLAlchemy.Member ).where(
            Doorbot.SQLAlchemy.Member.rfid == RFID_BAZ
        )
        member = session.scalars( member_fetch_stmt ).one()
        permissions = member.all_permissions()
        permission_names = [ x.name for x in permissions ]
        permission_names.sort()

        self.assertEqual( permission_names, [
            "back.door",
            "front.door",
            "woodshop.bandsaw",
            "woodshop.tablesaw",
        ], "Permissions found as expected" );

    def test_role_all_permissions( self ):
        session = Session( engine )

        role_fetch_stmt = select( Doorbot.SQLAlchemy.Role ).where(
            Doorbot.SQLAlchemy.Role.name == "doors"
        )
        role = session.scalars( role_fetch_stmt ).one()
        permissions = role.all_permissions()
        permission_names = [ x.name for x in permissions ]
        permission_names.sort()

        self.assertEqual( permission_names, [
            "back.door",
            "front.door",
        ], "Permissions found as expected" );
