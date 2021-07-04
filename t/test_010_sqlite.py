import unittest
import Doorbot.Config
import Doorbot.DB as DB
import Doorbot.DBSqlite3
import sqlite3


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


if __name__ == '__main__':
    unittest.main()
