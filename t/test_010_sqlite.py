import unittest
import Doorbot.Config
import Doorbot.DB as DB
import Doorbot.DBSqlite3
import sqlite3
import time


class TestDB( unittest.TestCase ):
    @classmethod
    def setUpClass( cls ):
        conn = sqlite3.connect( ':memory:', isolation_level = None )
        DB.set_db( conn )
        Doorbot.DBSqlite3.create()

    @classmethod
    def tearDownClass( cls ):
        DB.close()


    def test_member( self ):
        DB.add_member( "Foo Bar", "1234" )
        self.assertTrue( True, "Added member" )

        member = DB.fetch_member_by_name( "Foo Bar" )
        self.assertEqual(
            member[ 'rfid' ],
            "1234",
            "Fetched member by name",
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
        self.assertEqual( logs[0][ 'rfid' ], "8756", "Logs ordered correctly" )

        logs = DB.fetch_entries( 10 )
        self.assertEqual( len( logs ), 10, "Set limit on results" )

        logs = DB.fetch_entries( 10, 101 )
        self.assertLess( len( logs ), 10, "Offset caused few results to return" )
        self.assertNotEqual( logs[0][ 'rfid' ], "8756", "Offset results" )

        logs = DB.fetch_entries( 500 )
        self.assertGreater( len( logs ), 100, "Fetched everything" )
        self.assertEqual( logs[ -1 ][ 'rfid' ], "5678",
            "Logs ordered correctly" )


if __name__ == '__main__':
    unittest.main()
