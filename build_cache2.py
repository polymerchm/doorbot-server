#!/usr/bin/python3

"""
LIMITATIONS:
  There appears to be no 100% reliable way to get the ending date from the
    database as of 2023-10. As an example, a member had a membership paid
    annually plus a studio paid monthly. In the database, the latest_txn and all
    recent_transactions were for the monthly studio. And the active_memberships
    info doesn't include the ending date.
  A duplicate rfid db name may overwrite and hide a useful/active rfid db name.
    To prevent this, rfid db names should be required to be unique.
  A duplicate garbage mms name may overwrite and hide a useful/active mms name.
    (Example: garbage mms entries accidentally made with the events system)
    This has been alleviated (completely? mostly?) by not processing entries
    when there are zero recent_transactions in the entry.
TODO/ISSUES:
  As a double-check, it could/should look for and report duplicate rfid db names
    and duplicate mms names that have recent_transactions.
  This has not been tested to see if it behaves well if no entries are found.
"""
import requests
import json
import sys
import Doorbot.Config
from Doorbot.SQLAlchemy import Member
from Doorbot.SQLAlchemy import get_session
from sqlalchemy import select

conf = Doorbot.Config.get( 'memberpress' )
user = conf[ 'user' ]
passwd = conf[ 'passwd' ]
base_url = conf[ 'base_url' ]

members_url = base_url + '/wp-json/mp/v1/members'


def fetch_member_mms_page(
    page = 1,
    per_page = 100,
):
    print('.', end='', file=sys.stderr, flush=True)
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

def fetch_all_mms_members():
    is_still_more = True
    page = 1
    per_page = 100
    all_members = []

    while is_still_more:
        members = fetch_member_mms_page( page, per_page )

        if len( members ) != per_page:
            # If we didn't get as many members as expected, assume we've
            # reached the end of the list. Unfortunately, the MemberPress
            # API doesn't have any other way for us to know this.
            is_still_more = False

        if len( members ) != 0:
            all_members = all_members +  members

        page += 1

    return all_members

def reformat_mms_members( members ):
    results = {}
    for member in members:
        if len(member[ 'recent_transactions' ]) == 0 :
            continue;
        mms_id = member[ 'id' ]
        first_name = member[ 'first_name' ]
        last_name = member[ 'last_name' ]
        display_name = first_name + " " + last_name
        active_memberships = member[ 'active_memberships' ]
        end_date = '0000-00-00 00:00:00'
        mbrship = 0
        for trans in member[ 'recent_transactions' ]:
            if end_date < trans["expires_at"] and trans["status"] == "complete":
                end_date = trans["expires_at"]
                mbrship = trans["membership"]

        results[ display_name ] = {
            'display_name': display_name,
            'mms_id': mms_id,
            'active_tag': (
                False if len( active_memberships ) == 0 else True ),
            'active_memberships': active_memberships,
            'mbrship': mbrship,
            'end_date': end_date[:10],
        }

    return results

def fetch_members_db():
    session = get_session()
    stmt = select( Member )
    members = session.scalars( stmt ).all()

    results = {}
    for member in members:
        rfid = member.rfid
        name = member.full_name
        active = True if member.active else False
        mms_id = member.mms_id if member.mms_id else ""

        results[ name ] = {
            'display_name': name,
            'mms_id': mms_id,
            'active_tag': active,
            'rfid': rfid,
        }

    return results

def filter_members( db_members, mms_members ):
    clear_members = []
    wrong_name_members = []
    wrong_active_members = []
    no_mms_id_in_db_members = []
    wrong_rfid_name_members = []

    for mms_member in mms_members.values():
        name_mms = mms_member[ "display_name" ]

        if not name_mms in db_members:
            if mms_member[ "active_tag" ]:
                wrong_name_members.append({
                    'mms': mms_member,
                    'db': None,
                })
        else:
            db_member = db_members[ name_mms ]
            entry = {
                'mms': mms_member,
                'db': db_member,
            }

            if mms_member[ "active_tag" ] != db_member[ "active_tag" ]:
                wrong_active_members.append( entry )
            else:
                clear_members.append( entry )

            if not db_member[ 'mms_id' ]:
                no_mms_id_in_db_members.append( entry )

    for db_member in db_members.values():
        if not db_member[ "display_name" ] in mms_members and db_member[ "active_tag" ]:
            wrong_rfid_name_members.append({
                'mms': None,
                'db': db_member,
            })

    return clear_members, wrong_name_members, wrong_rfid_name_members, \
            wrong_active_members, no_mms_id_in_db_members

def handle_clear_members( members ):
    clear_members = map(
        lambda _ : {
            'rfid': _[ 'db' ][ 'rfid' ],
            'active_mms': _[ 'mms' ][ 'active_tag' ],
            'name_mms': _[ 'mms' ][ 'display_name' ],
        },
        members,
    )
    return list( clear_members )

def handle_wrong_name_members( members ):
    wrong_name_members = map(
        lambda _ : {
            'mms_id': _[ 'mms' ][ 'mms_id' ],
            'name_mms': _[ 'mms' ][ 'display_name' ],
        },
        members,
    )
    return list( wrong_name_members )

def handle_wrong_rfid_name_members( members ):
    wrong_rfid_name_members = map(
        lambda _ : {
            'rfid': _[ 'db' ][ 'rfid' ],
            'name_rfid': _[ 'db' ][ 'display_name' ],
        },
        members,
    )
    return list( wrong_rfid_name_members )

def handle_wrong_active_members( members ):
    wrong_active_members = map(
        lambda _ : {
            'rfid': _[ 'db' ][ 'rfid' ],
            'name_mms': _[ 'mms' ][ 'display_name' ],
            'active_mms': _[ 'mms' ][ 'active_tag' ],
            'active_db': _[ 'db' ][ 'active_tag' ],
            'mbrship': _[ 'mms' ][ 'mbrship' ],
            'end_date': _[ 'mms' ][ 'end_date' ],
        },
        members,
    )
    return list( wrong_active_members )

def handle_no_mms_id_in_db_members( members ):
    no_mms_id_in_db_members = map(
        lambda _ : {
            'rfid': _[ 'db' ][ 'rfid' ],
            'mms_id': _[ 'mms' ][ 'mms_id' ],
            'name_db': _[ 'db' ][ 'display_name' ],
            'end_date': _[ 'mms' ][ 'end_date' ],
        },
        members,
    )
    return list( no_mms_id_in_db_members )


print('reading mms.', end='', file=sys.stderr, flush=True)
members_raw = fetch_all_mms_members()
print(' ', end='', file=sys.stderr, flush=True)
members_list = reformat_mms_members( members_raw )

db_members_list = fetch_members_db()

clear_members, wrong_name_members, wrong_rfid_name_members, wrong_active_members, \
    no_mms_id_in_db_members = filter_members( db_members_list, members_list )

formatted_members = {
    'clear_members': handle_clear_members( clear_members ),
    'wrong_name_members': handle_wrong_name_members( wrong_name_members ),
    'wrong_rfid_name_members': handle_wrong_rfid_name_members( wrong_rfid_name_members ),
    'wrong_active_members': handle_wrong_active_members( wrong_active_members ),
    'no_mms_id_in_db_members': handle_no_mms_id_in_db_members( no_mms_id_in_db_members ),
}
json.dump( formatted_members, sys.stdout )
print('done.', file=sys.stderr, flush=True)
