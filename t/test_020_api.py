import unittest
import flask_unittest
import flask.globals
from flask import json
import os
import psycopg2
import re
import sqlite3
import Doorbot.Config
import Doorbot.DB as DB
import Doorbot.DBSqlite3
import Doorbot.API

USER_PASS = ( "user", "pass" )

class TestAPI( flask_unittest.ClientTestCase ):
    app = Doorbot.API.app

    @classmethod
    def setUpClass( cls ):
        if 'PG' == os.environ.get( 'DB' ):
            pg_conf = Doorbot.Config.get( 'postgresql' )
            user = pg_conf[ 'username' ]
            passwd = pg_conf[ 'passwd' ]
            database = pg_conf[ 'database' ]

            conn_str = ' '.join([
                'dbname=' + database,
                'user=' + user,
                'password=' + passwd,
            ])
            conn = psycopg2.connect( conn_str )
            conn.set_session( autocommit = True )
            DB.set_db( conn )
        else:
            conn = sqlite3.connect( ':memory:', isolation_level = None )
            DB.set_db( conn )
            DB.set_sqlite()
            Doorbot.DBSqlite3.create()

        global user_pass
        DB.add_member( "_tester", USER_PASS[0] )
        DB.set_password( USER_PASS[0], USER_PASS[1], {
            "type": "plaintext",
        })

    @classmethod
    def tearDownClass( cls ):
        DB.close()

    def test_check_tag( self, client ):
        global user_pass

        DB.add_member( "Foo Bar", "1234" )
        DB.add_member( "Foo Baz", "4321" )
        DB.deactivate_member( "4321" )

        rv = client.get( '/check_tag/1234', auth = USER_PASS )
        self.assertStatus( rv, 200 )

        rv = client.get( '/check_tag/4321', auth = USER_PASS )
        self.assertStatus( rv, 403 )

        rv = client.get( '/check_tag/1111', auth = USER_PASS )
        self.assertStatus( rv, 404 )

        rv = client.get( '/check_tag/foobar', auth = USER_PASS )
        self.assertStatus( rv, 400 )

    def test_entry_location( self, client ):
        DB.add_member( "Bar Baz", "5678" )
        DB.add_member( "Bar Qux", "8765" )
        DB.deactivate_member( "8765" )

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
        DB.add_member( "Qux Quux", "0123" )

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
        DB.add_member( "Bar Quuux", "09865" )
        DB.add_member( "Bar Quuuux", "98764" )
        DB.add_member( "Baz Quuux", "87653" )
        DB.add_member( "Baz Quuuux", "76542" )

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
        DB.add_member( "Bar Quuux", "09876" )
        DB.log_entry( "09876", "cleanroom.door", True, True )

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
        DB.add_member( "Qux Quuux", "45321" )
        DB.add_member( "Qux Quuuux", "12354" )
        DB.deactivate_member( "12354" )


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
