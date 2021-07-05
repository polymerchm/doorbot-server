import psycopg2
import sqlite3

CONN = None

INSERT_MEMBER = '''
    INSERT INTO members
        (full_name, rfid, phone, email)
    VALUES
        (?, ?, '', '')
'''
FETCH_MEMBER_BY_NAME = '''
    SELECT full_name, rfid, active
    FROM members
    WHERE full_name LIKE ?
'''
FETCH_MEMBER_BY_RFID = '''
    SELECT full_name, rfid, active
    FROM members
    WHERE rfid = ?
'''

LOG_ENTRY = '''
    INSERT INTO entry_log (
        rfid
        ,location_id
        ,is_active_tag
        ,is_found_tag
    ) VALUES (
        ?
        ,(SELECT id FROM locations WHERE name = ? LIMIT 1)
        ,?
        ,?
    )
'''
FETCH_ENTRIES = '''
    SELECT
        entry_log.rfid
        ,locations.name
        ,entry_log.is_active_tag
        ,entry_log.is_found_tag
    FROM entry_log
    JOIN locations ON entry_log.location_id = locations.id
    ORDER BY entry_time DESC
    LIMIT ?
    OFFSET ?
'''

SET_MEMBER_ACTIVE_STATUS = '''
    UPDATE members
    SET active = ?
    WHERE rfid = ?
'''

def set_db( conn ):
    global CONN
    CONN = conn

def conn():
    return CONN

def close():
    CONN.close()


def add_member(
    name: str,
    rfid: str,
):
    sql = conn()
    cur = sql.cursor()
    cur.execute( INSERT_MEMBER, ( name, rfid ) )
    cur.close()
    return

def fetch_member_by_name(
    name: str,
):
    name = name + '%'

    sql = conn()
    cur = sql.cursor()
    cur.execute( FETCH_MEMBER_BY_NAME, [ name ] )
    row = cur.fetchone()
    cur.close()

    if None == row:
        return None
    else:
        member = {
            'full_name': row[0],
            'rfid': row[1],
            'is_active': True if row[2] else False,
        }
        return member

def fetch_member_by_rfid(
    rfid: str,
):
    sql = conn()
    cur = sql.cursor()
    cur.execute( FETCH_MEMBER_BY_RFID, [ rfid ] )
    row = cur.fetchone()
    cur.close()

    if None == row:
        return None
    else:
        member = {
            'full_name': row[0],
            'rfid': row[1],
            'is_active': True if row[2] else False,
        }
        return member

def log_entry(
    rfid: str,
    location: str,
    is_active_tag: bool,
    is_found_tag: bool,
):
    sql = conn()
    cur = sql.cursor()
    cur.execute( LOG_ENTRY, [ rfid, location, is_active_tag, is_found_tag ] )
    cur.close()
    return

def _map_entry( entry ):
    result = {
        'rfid': entry[0],
        'name': entry[1],
        'is_active_tag': True if entry[2] else False,
        'is_found_tag': True if entry[3] else False,
    }
    return result

def fetch_entries(
    limit: int = 100,
    offset: int = 0,
):
    sql = conn()
    cur = sql.cursor()
    cur.execute( FETCH_ENTRIES, [ limit, offset ] )
    rows = cur.fetchall()
    cur.close()

    results = map(
        _map_entry,
        rows,
    )
    return list( results )

def deactivate_member(
    rfid: str
):
    sql = conn()
    cur = sql.cursor()
    cur.execute( SET_MEMBER_ACTIVE_STATUS, ( False, rfid ) )
    cur.close()
    return

def activate_member(
    rfid: str
):
    sql = conn()
    cur = sql.cursor()
    cur.execute( SET_MEMBER_ACTIVE_STATUS, ( True, rfid ) )
    cur.close()
    return

def _map_search_members( entry ):
    result = {
        'rfid': entry[0],
        'full_name': entry[1],
        'active': True if entry[2] else False,
    }
    return result

def search_members(
    full_name: str,
    rfid: str,
    offset: int,
    limit: int,
):
    where = []
    end = []
    params = []

    if full_name:
        where.append( 'lower(full_name) LIKE ?' )
        params.append( full_name + '%' )

    if rfid:
        where.append( 'rfid = ?' )
        params.append( rfid )

    if limit or offset:
        end.append( 'ORDER BY join_date' )

    if limit:
        end.append( 'LIMIT ?' )
        params.append( limit )

    if offset:
        end.append( 'OFFSET ?' )
        params.append( offset )



    statement = ' '.join([
        'SELECT rfid, full_name, active FROM members'
        ' WHERE ' if where else '',
        ' AND '.join( where ),
        ' '.join( end ),
    ])

    sql = conn()
    cur = sql.cursor()
    cur.execute( statement, params )
    rows = cur.fetchall()
    cur.close()

    results = map(
        _map_search_members,
        rows,
    )
    return list( results )

