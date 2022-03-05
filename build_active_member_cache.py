#!/usr/bin/python3
import requests
import Doorbot.Config
import psycopg2


DEFAULT_RFID = "0000000000"

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
    zero_rfid = []
    for member in members:
        rfid = member[ 'profile' ][ 'mepr_keyfob_id' ]
        mms_id = member[ 'id' ]
        first_name = member[ 'first_name' ]
        last_name = member[ 'last_name' ]
        email = member[ 'email' ]
        active_memberships = member[ 'active_memberships' ]

        # Pad RFID tags with leading zeros
        rfid = rfid.zfill( 10 )

        entry = {
            'mms_id': mms_id,
            'display_name': first_name + " " + last_name,
            'email': email,
            'active_memberships': active_memberships,
            'rfid': rfid,
        }
        entry[ 'is_active_tag' ] = is_active_member( entry )

        if DEFAULT_RFID == rfid:
            zero_rfid.append( entry )
        else:
            by_rfid[ rfid ] = entry

    return by_rfid, zero_rfid


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

def filter_members( db_members, mms_members ):
    clear_members = []
    wrong_name_members = []
    wrong_active_members = []
    add_to_db_members = []
    add_to_mms_members = []

    for mms_member in mms_members.values():
        rfid = mms_member[ "rfid" ]
        name_mms = mms_member[ "display_name" ]
        is_active_mms = mms_member[ "is_active_tag" ]

        if not rfid in db_members:
            add_to_db_members.append({
                'mms': mms_member,
                'db': None,
            })
        else:
            db_member = db_members[ rfid ]
            entry = {
                'mms': mms_member,
                'db': db_member,
            }

            if is_active_mms != db_member[ "is_active_tag" ]:
                wrong_active_members.append( entry )
            else:
                name_db = db_members[ rfid ][ "display_name" ]
                if name_mms != name_db:
                    wrong_name_members.append( entry )
                else:
                    clear_members.append( entry )

    add_to_mms_members = []
    for rfid in db_members.keys():
        if not rfid in mms_members:
            db_member = db_members[ rfid ]
            add_to_mms_members.append({
                'mms': None,
                'db': db_member,
            })

    return clear_members, wrong_name_members, wrong_active_members, add_to_db_members, add_to_mms_members

def handle_clear_members( members ):
    for member in members:
        rfid = member[ 'mms' ][ 'rfid' ]
        print( f'{rfid} matches, do nothing' )

def handle_zero_rfid_members( members ):
    for member in members:
        mms_id = member[ 'mms_id' ]
        name = member[ 'display_name' ]
        print( f'MMS Member ID #{mms_id} |{name}| has zero\'d out RFID' )

def handle_wrong_name_members( members ):
    for member in members:
        rfid = member[ 'mms' ][ 'rfid' ]
        name_mms = member[ 'mms' ][ 'display_name' ]
        name_db = member[ 'db' ][ 'display_name' ]
        print( f'{rfid} is named |{name_mms}| in MMS, but |{name_db}| in DB, rectify' )

def handle_wrong_active_members( members ):
    for member in members:
        rfid = member[ 'mms' ][ 'rfid' ]
        name_mms = member[ 'mms' ][ 'display_name' ]
        is_active_mms = member[ 'mms' ][ 'is_active_tag' ]
        is_active_db = member[ 'db' ][ 'is_active_tag' ]
        print( f'{rfid} |{name_mms}| is {is_active_mms} in MMS, but {is_active_db} in DB, rectify' )


def handle_add_to_db_members( members ):
    for member in members:
        rfid = member[ 'mms' ][ 'rfid' ]
        name_mms = member[ 'mms' ][ 'display_name' ]
        print( f'{rfid} |{name_mms}| is in MMS, but not DB, add' )

def handle_add_to_mms_members( members ):
    for member in members:
        rfid = member[ 'db' ][ 'rfid' ]
        name_db = member[ 'db' ][ 'display_name' ]
        print( f'{rfid} |{name_db}| is in DB, but not MMS, add' )



db = db_connect()
members = fetch_all_members()
members_by_rfid, zero_rfid_members = map_members_by_rfid( members )

db_members_by_rfid = fetch_members_db( db )

clear_members, wrong_name_members, wrong_active_members, add_to_db_members, add_to_mms_members = filter_members( db_members_by_rfid, members_by_rfid )

handle_clear_members( clear_members )
handle_zero_rfid_members( zero_rfid_members )
handle_wrong_name_members( wrong_name_members )
handle_wrong_active_members( wrong_active_members )
handle_add_to_db_members( add_to_db_members )
handle_add_to_mms_members( add_to_mms_members )
print( f'Count {len( members )} members in MMS, {len( db_members_by_rfid.keys() )} in DB' )
