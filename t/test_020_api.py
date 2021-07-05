import unittest
import flask_unittest
import flask.globals
import re
import sqlite3
import Doorbot.Config
import Doorbot.DB as DB
import Doorbot.DBSqlite3
import Doorbot.API


class TestAPI( flask_unittest.ClientTestCase ):
    app = Doorbot.API.app

    @classmethod
    def setUpClass( cls ):
        conn = sqlite3.connect( ':memory:', isolation_level = None )
        DB.set_db( conn )
        Doorbot.DBSqlite3.create()

    @classmethod
    def tearDownClass( cls ):
        DB.close()

    def test_check_tag( self, client ):
        DB.add_member( "Foo Bar", "1234" )
        DB.add_member( "Foo Baz", "4321" )
        DB.deactivate_member( "4321" )

        rv = client.get( '/check_tag/1234' )
        self.assertStatus( rv, 200 )

        rv = client.get( '/check_tag/4321' )
        self.assertStatus( rv, 403 )

        rv = client.get( '/check_tag/1111' )
        self.assertStatus( rv, 404 )

        rv = client.get( '/check_tag/foobar' )
        self.assertStatus( rv, 400 )

    def test_entry_location( self, client ):
        DB.add_member( "Bar Baz", "5678" )
        DB.add_member( "Bar Qux", "8765" )
        DB.deactivate_member( "8765" )

        rv = client.get( '/entry/5678/cleanroom.door' )
        self.assertStatus( rv, 200 )

        rv = client.get( '/entry/8765/cleanroom.door' )
        self.assertStatus( rv, 403 )

        rv = client.get( '/entry/1111/cleanroom.door' )
        self.assertStatus( rv, 404 )

        rv = client.get( '/entry/foobar/cleanroom.door' )
        self.assertStatus( rv, 400 )

    def add_tag( self, client ):
        rv = client.get( '/check_tag/9012' )
        self.assertStatus( rv, 404 )

        rv = client.put( '/secure/new_tag/9012' )
        self.assertStatus( rv, 201 )

        rv = client.get( '/check_tag/9012' )
        self.assertStatus( rv, 200 )

    def test_activate_deactivate_member( self, client ):
        DB.add_member( "Qux Quux", "0123" )

        rv = client.get( '/check_tag/0123' )
        self.assertStatus( rv, 200 )

        rv = client.post( '/secure/deactivate_tag/0123' )
        self.assertStatus( rv, 200 )

        rv = client.get( '/check_tag/0123' )
        self.assertStatus( rv, 403 )

        rv = client.post( '/secure/reactivate_tag/0123' )
        self.assertStatus( rv, 200 )

        rv = client.get( '/check_tag/0123' )
        self.assertStatus( rv, 200 )

    def test_search( self, client ):
        DB.add_member( "Bar Quuux", "09876" )
        DB.add_member( "Bar Quuuux", "67890" )
        DB.add_member( "Baz Quuux", "98765" )
        DB.add_member( "Baz Quuuux", "56789" )

        match_bar = re.compile( '.*,bar.*', flags = re.I )

        rv = client.get( '/secure/search_tags?name=Bar&offset=0&limit=1' )
        data = rv.data.decode( "UTF-8" )
        self.assertTrue(
            match_bar.match( data ),
            "Matched bar",
        )


if __name__ == '__main__':
    unittest.main()
