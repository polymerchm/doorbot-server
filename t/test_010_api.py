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

class TestAPI( flask_unittest.ClientTestCase ):
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

        location = Doorbot.SQLAlchemy.Location(
            name = "cleanroom.door",
        )

        session = Session( engine )
        session.add_all([ member, location ])
        session.commit()

    def test_check_tag( self, client ):
        members = [
            Doorbot.SQLAlchemy.Member(
                full_name = "Foo Bar",
                rfid = "1234",
            ),
            Doorbot.SQLAlchemy.Member(
                full_name = "Foo Baz",
                rfid = "4321",
                active = False,
            ),
        ]
        session = Session( engine )
        session.add_all( members )
        session.commit()

        rv = client.get( '/check_tag/1234', auth = USER_PASS )
        self.assertStatus( rv, 200 )

        rv = client.get( '/check_tag/4321', auth = USER_PASS )
        self.assertStatus( rv, 403 )

        rv = client.get( '/check_tag/1111', auth = USER_PASS )
        self.assertStatus( rv, 404 )

        rv = client.get( '/check_tag/foobar', auth = USER_PASS )
        self.assertStatus( rv, 400 )

    def test_entry_location( self, client ):
        members = [
            Doorbot.SQLAlchemy.Member(
                full_name = "Bar Baz",
                rfid = "5678",
            ),
            Doorbot.SQLAlchemy.Member(
                full_name = "Bar Qux",
                rfid = "8765",
                active = False,
            ),
        ]
        session = Session( engine )
        session.add_all( members )
        session.commit()

        rv = client.get( '/entry/5678/cleanroom.door', auth = USER_PASS )
        self.assertStatus( rv, 200 )

        rv = client.get( '/entry/8765/cleanroom.door', auth = USER_PASS )
        self.assertStatus( rv, 403 )

        rv = client.get( '/entry/1111/cleanroom.door', auth = USER_PASS )
        self.assertStatus( rv, 404 )

        rv = client.get( '/entry/foobar/cleanroom.door', auth = USER_PASS )
        self.assertStatus( rv, 400 )

    def test_add_tag( self, client ):
        rv = client.get( '/check_tag/9012', auth = USER_PASS )
        self.assertStatus( rv, 404 )

        rv = client.put( '/secure/new_tag/9012/foo', auth = USER_PASS )
        self.assertStatus( rv, 201 )

        rv = client.get( '/check_tag/9012', auth = USER_PASS )
        self.assertStatus( rv, 200 )

    def test_activate_deactivate_member( self, client ):
        members = [
            Doorbot.SQLAlchemy.Member(
                full_name = "Qux Quux",
                rfid = "0123",
            ),
        ]
        session = Session( engine )
        session.add_all( members )
        session.commit()

        rv = client.get( '/check_tag/0123', auth = USER_PASS )
        self.assertStatus( rv, 200 )

        rv = client.post( '/secure/deactivate_tag/0123', auth = USER_PASS )
        self.assertStatus( rv, 200 )

        rv = client.get( '/check_tag/0123', auth = USER_PASS )
        self.assertStatus( rv, 403 )

        rv = client.post( '/secure/reactivate_tag/0123', auth = USER_PASS )
        self.assertStatus( rv, 200 )

        rv = client.get( '/check_tag/0123', auth = USER_PASS )
        self.assertStatus( rv, 200 )

    def test_search_tags( self, client ):
        members = [
            Doorbot.SQLAlchemy.Member(
                full_name = "Bar Quuux",
                rfid = "09865",
            ),
            Doorbot.SQLAlchemy.Member(
                full_name = "Bar Quuuux",
                rfid = "98764",
            ),
            Doorbot.SQLAlchemy.Member(
                full_name = "Baz Quuux",
                rfid = "87653",
            ),
            Doorbot.SQLAlchemy.Member(
                full_name = "Baz Quuuux",
                rfid = "76542",
            ),
        ]
        session = Session( engine )
        session.add_all( members )
        session.commit()

        match_bar = re.compile( '.*,.*Bar.*', re.MULTILINE | re.DOTALL | re.I )
        match_quuux = re.compile( '.*,.*quuux.*', flags = re.I )

        rv = client.get( '/secure/search_tags?name=Bar&offset=0&limit=1',
            auth = USER_PASS )
        data = rv.data.decode( "UTF-8" )
        self.assertTrue(
            match_bar.match( data ),
            "Matched bar",
        )

        rv = client.get( '/secure/search_tags?name=bar&offset=0&limit=1',
            auth = USER_PASS )
        data = rv.data.decode( "UTF-8" )
        self.assertTrue(
            match_bar.match( data ),
            "Matched bar in a case insensitive way",
        )

        rv = client.get( '/secure/search_tags?name=quuux&offset=0&limit=1',
            auth = USER_PASS )
        data = rv.data.decode( "UTF-8" )
        self.assertTrue(
            match_quuux.match( data ),
            "Matched quuux in a case insensitive way",
        )

    def test_search_entry_log( self, client ):
        # TODO partially converted; see Doorbot.API.search_entry_log()
        return
        session = Session( engine )
        stmt = select( Doorbot.SQLAlchemy.Location ).where(
            Doorbot.SQLAlchemy.Location.name == "cleanroom.door"
        )
        location = session.scalars( stmt ).one()

        entries = [
            Doorbot.SQLAlchemy.Member(
                full_name = "Bar Quuux",
                rfid = "09876",
            ),
            Doorbot.SQLAlchemy.EntryLog(
                rfid = "09876",
                is_active_tag = True,
                is_found_tag = True,
                mapped_location = location,
            ),
        ]
        session.add_all( entries )
        session.commit()

        match_cleanroom = re.compile( '.*,cleanroom\.door.*',
            re.MULTILINE | re.DOTALL )

        rv = client.get( '/secure/search_entry_log?tag=09876&offset=0&limit=1',
            auth = USER_PASS )
        data = rv.data.decode( "UTF-8" )
        self.assertTrue(
            match_cleanroom.match( data ),
            "Matched RFID tag",
        )

        # Test for blank location
        DB.log_entry( "09876", None, True, True )
        rv = client.get( '/secure/search_entry_log', auth = USER_PASS )
        data = rv.data.decode( "UTF-8" )
        self.assertTrue(
            match_cleanroom.match( data ),
            "Matched bar",
        )

    def test_dump_tags( self, client ):
        members = [
            Doorbot.SQLAlchemy.Member(
                full_name = "QUX Quuux",
                rfid = "45321",
            ),
            Doorbot.SQLAlchemy.Member(
                full_name = "Qux Quuuux",
                rfid = "12354",
                active = False,
            ),
        ]
        session = Session( engine )
        session.add_all( members )
        session.commit()


        rv = client.get( '/secure/dump_active_tags', auth = USER_PASS )
        data = rv.data.decode( "UTF-8" )
        data = json.loads( data )

        self.assertTrue(
            "45321" in data,
            "Fetched active member",
        )
        self.assertFalse(
            "12354" in data,
            "Did not fetch deactivated member",
        )

    def test_edit_tag( self, client ):
        rv = client.get( '/check_tag/09017', auth = USER_PASS )
        self.assertStatus( rv, 404 )

        rv = client.get( '/check_tag/19017', auth = USER_PASS )
        self.assertStatus( rv, 404 )

        # Create tag
        rv = client.put( '/secure/new_tag/09017/foo', auth = USER_PASS )
        self.assertStatus( rv, 201 )

        rv = client.get( '/check_tag/09017', auth = USER_PASS )
        self.assertStatus( rv, 200 )

        rv = client.get( '/check_tag/19017', auth = USER_PASS )
        self.assertStatus( rv, 404 )

        # Edit tag
        rv = client.post( '/secure/edit_tag/09017/19017', auth = USER_PASS )
        self.assertStatus( rv, 201 )

        rv = client.get( '/check_tag/09017', auth = USER_PASS )
        self.assertStatus( rv, 404 )

        rv = client.get( '/check_tag/19017', auth = USER_PASS )
        self.assertStatus( rv, 200 )

    def test_edit_name( self, client ):
        rv = client.get( '/check_tag/29017', auth = USER_PASS )
        self.assertStatus( rv, 404 )

        rv = client.get( '/check_tag/29017', auth = USER_PASS )
        self.assertStatus( rv, 404 )

        # Create tag
        rv = client.put( '/secure/new_tag/29017/foo', auth = USER_PASS )
        self.assertStatus( rv, 201 )

        rv = client.get( '/check_tag/29017', auth = USER_PASS )
        self.assertStatus( rv, 200 )

        # Edit tag
        rv = client.post( '/secure/edit_name/29017/bar', auth = USER_PASS )
        self.assertStatus( rv, 201 )


if __name__ == '__main__':
    unittest.main()
