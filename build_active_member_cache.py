#!/usr/bin/python3
import requests
import Doorbot.Config


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

        by_rfid[ rfid ] = {
            'mms_id': mms_id,
            'display_name': display_name,
            'email': email,
            'active_memberships': active_memberships,
            'rfid': rfid,
        }

    return by_rfid


def is_active_member( member ):
    member_email = member[ 'email' ]
    member_id = member[ 'mms_id' ]

    if len( member[ 'active_memberships' ] ) == 0:
        print( f'{member_email} (id {member_id}) is not active, skipping' )
        return False
    if member[ 'rfid' ] == "":
        print( f'{member_email} (id {member_id}) has no keyfob, skipping' )
        return False
    if member[ 'rfid' ] == "0000000000":
        print( f'{member_email} (id {member_id}) has default keyfob, skipping' )
        return False

    print( f'{member_email} (id {member_id}) is active' )
    return True


members = fetch_all_members()
members_by_rfid = map_members_by_rfid( members )
print( "Filtering members" )
active_members = list( filter(
    is_active_member,
    members_by_rfid.values(),
) )
print( f'Count {len( active_members )} active members' )
