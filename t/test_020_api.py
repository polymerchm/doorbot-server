import flask_unittest
import flask.globals
import sqlite3
import Doorbot.Config
import Doorbot.DB as DB
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
        DB.add_member( "Foo Bar", "4321" )
        DB.deactivate_member( "4321" )

        rv = client.get( '/check_tag/1234' )
        self.assertStatus( rv, 200 )

        rv = client.get( '/check_tag/4321' )
        self.assertStatus( rv, 403 )

        rv = client.get( '/check_tag/1111' )
        self.assertStatus( rv, 404 )

        rv = client.get( '/check_tag/foobar' )
        self.assertStatus( rv, 400 )


if __name__ == '__main__':
    unittest.main()
