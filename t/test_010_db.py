import unittest
import Doorbot.Config
import Doorbot.DB as DB
import Doorbot.DBSqlite3
import os
import psycopg2
import sqlite3
import time


class TestDB( unittest.TestCase ):
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
            DB.set_db( conn )
        else:
            conn = sqlite3.connect( ':memory:', isolation_level = None )
            DB.set_db( conn )
            DB.set_sqlite()
            Doorbot.DBSqlite3.create()

    @classmethod
    def tearDownClass( cls ):
        DB.close()


    def test_member( self ):
        DB.add_member( "Foo Bar", "1234" )
        DB.add_member( "Fooo Bar", "12345" )
        self.assertTrue( True, "Added member" )

        member = DB.fetch_member_by_name( "Foo Bar" )
        self.assertEqual(
            member[ 'rfid' ],
            "1234",
            "Fetched member by name",
        )
        self.assertTrue(
            member[ 'is_active' ],
            "Member is active",
        )

        member = DB.fetch_member_by_name( "Foo" )
        self.assertEqual(
            member[ 'rfid' ],
            "1234",
            "Fetched member by name prefix",
        )
        
        member = DB.fetch_member_by_rfid( "1234" )
        self.assertEqual(
            member[ 'full_name' ],
            "Foo Bar",
            "Fetched member by RFID",
        )

        member = DB.fetch_member_by_name( "Bar Foo" )
        self.assertEqual(
            member,
            None,
            "No member found for name",
        )

        member = DB.fetch_member_by_rfid( "4321" )
        self.assertEqual(
            member,
            None,
            "No member found for rfid",
        )

        DB.deactivate_member( "1234" )
        member = DB.fetch_member_by_rfid( "1234" )
        self.assertFalse(
            member[ 'is_active' ],
            "Member no longer active",
        )

        DB.activate_member( "1234" )
        member = DB.fetch_member_by_rfid( "1234" )
        self.assertTrue(
            member[ 'is_active' ],
            "Member is active again",
        )

        members = DB.search_members( "foo", None, 0, 1 )
        self.assertEqual( len( members ), 1, "Returned one result" )

        members = DB.search_members( "foo", "", 0, 5 )
        self.assertEqual( len( members ), 2, "Returned both results" )

        members = DB.search_members( "foo", None, 1, 5 )
        self.assertEqual( len( members ), 1, "Returned offset results" )

    def test_entry_log( self ):
        DB.add_member( "Bar Qux", "5678" )
        DB.log_entry( "5678", "cleanroom.door", True, True )

        # Wait a second so the entry above will be ordered last by datetime
        time.sleep( 1 )
        DB.log_entry( "8765", "garage.door", False, False )
        DB.log_entry( "8756", "woodshop.door", False, True )

        # Wait a second so the entries above will be ordered last by datetime
        time.sleep( 1 )
        for i in range( 101 ):
            DB.log_entry( "8756", "garage.door", False, False )

        self.assertTrue( True, "Created entry logs" )


        logs = DB.fetch_entries()
        self.assertEqual( len( logs ), 100, "Default limit of 100" )

        # Ordering and offset doesn't always work right on PG, because we're
        # not isolated from other tests running. Ignore this test on PG for now.
        # TODO make this work
        if 'PG' != os.environ.get( 'DB' ):
            self.assertEqual( logs[0][ 'rfid' ], "8756",
                "Logs ordered correctly" )

        logs = DB.fetch_entries( 10 )
        self.assertEqual( len( logs ), 10, "Set limit on results" )

        logs = DB.fetch_entries( 10, 101 )
        self.assertLess( len( logs ), 10, "Offset caused few results to return" )
        # See above about offset on PG
        if 'PG' != os.environ.get( 'DB' ):
            self.assertNotEqual( logs[0][ 'rfid' ], "8756", "Offset results" )

        logs = DB.fetch_entries( 500 )
        self.assertGreater( len( logs ), 100, "Fetched everything" )
        # See above about ordering on PG
        if 'PG' != os.environ.get( 'DB' ):
            self.assertEqual( logs[ -1 ][ 'rfid' ], "5678",
                "Logs ordered correctly" )

    def test_dump_all( self ):
        DB.add_member( "Baz Quux", "67890" )
        DB.add_member( "Baz Quuux", "67891" )
        DB.deactivate_member( "67891" )

        members = DB.dump_active_members()
        self.assertTrue( "67890" in members, "Active key in dump" )
        self.assertFalse( "67891" in members, "Deactivated key not in dump" )


if __name__ == '__main__':
    unittest.main()
