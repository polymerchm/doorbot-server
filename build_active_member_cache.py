#!/usr/bin/python3
import requests
import Doorbot.Config
import psycopg2


conf = Doorbot.Config.get( 'memberpress' )
user = conf[ 'user' ]
passwd = conf[ 'passwd' ]
base_url = conf[ 'base_url' ]

members_url = base_url + '/wp-json/mp/v1/members'


def fetch_member_page(
    page = 1,
    per_page = 100,
):
    response = requests.get(
        members_url + f'?page={page}&per_page={per_page}',
        auth = (
            user,
            passwd,
        ),
    )
    if 200 == response.status_code:
        data = response.json()
        return data

def fetch_all_members():
    is_still_more = True
    page = 1
    per_page = 100
    all_members = []

    while is_still_more:
        members = fetch_member_page( page, per_page )
        print( f'Fetched {len( members )} members' )

        if len( members ) != per_page:
            # If we didn't get as many members as expected, assume we've 
            # reached the end of the list. Unfortunately, the MemberPress
            # API doesn't have any other way for us to know this.
            is_still_more = False
            print( f'Reached the end of the member list on page {page}' )

        if len( members ) != 0:
            all_members = all_members +  members

        page += 1

    print( f'Fetched {len( all_members )} members' )
    return all_members

def map_members_by_rfid( members ):
    by_rfid = {}
    for member in members:
        rfid = member[ 'profile' ][ 'mepr_keyfob_id' ]
        mms_id = member[ 'id' ]
        display_name = member[ 'display_name' ]
        email = member[ 'email' ]
        active_memberships = member[ 'active_memberships' ]

        # Pad RFID tags with leading zeros
        rfid = rfid.zfill( 10 )

        by_rfid[ rfid ] = {
            'mms_id': mms_id,
            'display_name': display_name,
            'email': email,
            'active_memberships': active_memberships,
            'rfid': rfid,
        }
        by_rfid[ rfid ][ "is_active_tag" ] = is_active_member(
            by_rfid[ rfid ] )

    return by_rfid


def is_active_member( member ):
    member_email = member[ 'email' ]
    member_id = member[ 'mms_id' ]

    if len( member[ 'active_memberships' ] ) == 0:
        return False
    if member[ 'rfid' ] == "":
        return False
    if member[ 'rfid' ] == "0000000000":
        return False

    return True

def db_connect():
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
    return conn

def fetch_members_db( db ):
    cur = db.cursor()
    cur.execute( "SELECT rfid, full_name, active FROM members" )
    rows = cur.fetchall()
    cur.close()

    results = {}
    for member in rows:
        rfid = member[0]
        name = member[1]
        active = member[2]

        results[ rfid ] = {
            'rfid': rfid,
            'display_name': name,
            'is_active_tag': True if active else False,
        }

    return results

def iterate_members( db_members, mms_members ):
    db_members_filtered = db_members.copy()
    mms_members_filtered = mms_members.copy()

    for mms_member in mms_members.values():
        rfid = mms_member[ "rfid" ]
        if rfid in db_members_filtered:
            if mms_member[ "is_active_tag" ] == db_members_filtered[ rfid ][ "is_active_tag" ]:
                print( f'{rfid} matches, do nothing' )
            else:
                print( f'{rfid} is {mms_member[ "is_active_tag" ]} in MMS, but {db_members_filtered[ rfid ][ "is_active_tag" ]} in DB, rectify' )
        else:
            print( f'{rfid} is in MMS, but not DB, add' )

members = fetch_all_members()
members_by_rfid = map_members_by_rfid( members )

db = db_connect()
db_members_by_rfid = fetch_members_db( db )

iterate_members( db_members_by_rfid, members_by_rfid )
print( f'Count {len( members )} members in MMS, {len( db_members_by_rfid.keys() )} in DB' )
