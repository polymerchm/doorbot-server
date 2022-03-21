#!/usr/bin/python3
import requests
import json
import Doorbot.Config
import Doorbot.DB as DB
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

        if len( members ) != per_page:
            # If we didn't get as many members as expected, assume we've 
            # reached the end of the list. Unfortunately, the MemberPress
            # API doesn't have any other way for us to know this.
            is_still_more = False

        if len( members ) != 0:
            all_members = all_members +  members

        page += 1

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
    host = pg_conf[ 'host' ]
    port = pg_conf[ 'port' ]

    conn_str = ' '.join([
        'dbname=' + database,
        'user=' + user,
        'password=' + passwd,
        #'host=' + host,
        #'port=' + str( port ),
    ])

    conn = psycopg2.connect( conn_str )
    conn.set_session( autocommit = True )
    return conn

def fetch_members_db( db ):
    cur = db.cursor()
    cur.execute( "SELECT rfid, full_name, active, mms_id FROM members" )
    rows = cur.fetchall()
    cur.close()

    results = {}
    for member in rows:
        rfid = member[0]
        name = member[1]
        active = member[2]
        mms_id = member[3]

        results[ rfid ] = {
            'rfid': rfid,
            'display_name': name,
            'is_active_tag': True if active else False,
            'mms_id': mms_id,
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
    no_mms_id_in_db_members = []
    for rfid in db_members.keys():
        db_member = db_members[ rfid ]

        if not rfid in mms_members:
            add_to_mms_members.append({
                'mms': None,
                'db': db_member,
            })

        if not db_member[ 'mms_id' ] and rfid in mms_members:
            mms_member = mms_members[ rfid ]
            no_mms_id_in_db_members.append({
                'mms': mms_member,
                'db': db_member,
            })

    return clear_members, wrong_name_members, wrong_active_members, add_to_db_members, add_to_mms_members, no_mms_id_in_db_members

def handle_clear_members( members ):
    clear_members = map(
        lambda _ : { 'rfid': _[ 'mms' ][ 'rfid' ] },
        members,
    )
    return list( clear_members )

def handle_zero_rfid_members( members ):
    zerod_members = map(
        lambda _ : {
            'mms_id': _[ 'mms_id' ],
            'display_name': _[ 'display_name' ],
        },
        members,
    )
    return list( zerod_members )

def handle_wrong_name_members( members ):
    wrong_name_members = map(
        lambda _ : {
            'rfid': _[ 'mms' ][ 'rfid' ],
            'name_mms': _[ 'mms' ][ 'display_name' ],
            'name_db': _[ 'db' ][ 'display_name' ],
        },
        members,
    )
    return list( wrong_name_members )

def handle_wrong_active_members( members ):
    wrong_active_members = map(
        lambda _ : {
            'rfid': _[ 'mms' ][ 'rfid' ],
            'name_mms': _[ 'mms' ][ 'display_name' ],
            'is_active_mms': _[ 'mms' ][ 'is_active_tag' ],
            'is_active_db': _[ 'db' ][ 'is_active_tag' ],
        },
        members,
    )
    return list( wrong_active_members )

def handle_add_to_db_members( members ):
    add_to_db_members = map(
        lambda _ : {
            'rfid': _[ 'mms' ][ 'rfid' ],
            'name_mms': _[ 'mms' ][ 'display_name' ],
            'mms_id': _[ 'mms' ][ 'mms_id' ]
        },
        members,
    )
    return list( add_to_db_members )

def handle_add_to_mms_members( members ):
    add_to_mms_members = map(
        lambda _ : {
            'rfid': _[ 'db' ][ 'rfid' ],
            'name_db': _[ 'db' ][ 'display_name' ],
        },
        members,
    )
    return list( add_to_mms_members )

def handle_no_mms_id_in_db_members( members ):
    no_mms_id_in_db_members = map(
        lambda _ : {
            'rfid': member[ 'db' ][ 'rfid' ],
            'mms_id': member[ 'mms' ][ 'mms_id' ],
            'name_db': member[ 'db' ][ 'display_name' ],
        },
        members,
    )
    return list( no_mms_id_in_db_members )
        #cur = db.cursor()
        #cur.execute(
        #    "UPDATE members SET mms_id = %s WHERE rfid = %s",
        #    ( mms_id, rfid ),
        #)
        #cur.close()



db = db_connect()
DB.set_db( db )

members = fetch_all_members()
members_by_rfid, zero_rfid_members = map_members_by_rfid( members )

db_members_by_rfid = fetch_members_db( db )

clear_members, wrong_name_members, wrong_active_members, add_to_db_members, add_to_mms_members, no_mms_id_in_db_members = filter_members( db_members_by_rfid, members_by_rfid )

formatted_members = {
    'clear_members': handle_clear_members( clear_members ),
    'zerod_members': handle_zero_rfid_members( zero_rfid_members ),
    'wrong_name_members': handle_wrong_name_members( wrong_name_members ),
    'wrong_active_members': handle_wrong_active_members( wrong_active_members ),
    'add_to_db_members': handle_add_to_db_members( add_to_db_members ),
    'add_to_mms_members': handle_add_to_mms_members( add_to_mms_members ),
    'no_mms_id_in_db_members': handle_no_mms_id_in_db_members( no_mms_id_in_db_members ),
}
print( json.dumps( formatted_members ) )
