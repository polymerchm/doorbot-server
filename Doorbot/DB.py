import base64
import bcrypt
import hashlib
import psycopg2
import re
import sqlite3
import sys
import time
import Doorbot.Config

PASSWORD_TYPE_PLAINTEXT = "plaintext"
PASSWORD_TYPE_BCRYPT = "bcrypt"

CONN = None

INSERT_MEMBER = '''
    INSERT INTO members
        (full_name, rfid, phone, email, entry_type, mms_id)
    VALUES
        (%s, %s, '', '', '', %s)
'''
FETCH_MEMBER_BY_NAME = '''
    SELECT full_name, rfid, active, mms_id
    FROM members
    WHERE full_name ILIKE %s
'''
FETCH_MEMBER_BY_RFID = '''
    SELECT id, full_name, rfid, active, mms_id
    FROM members
    WHERE rfid = %s
'''

LOG_ENTRY = '''
    INSERT INTO entry_log (
        rfid
        ,location
        ,is_active_tag
        ,is_found_tag
    ) VALUES (
        %s
        ,(SELECT id FROM locations WHERE name = %s LIMIT 1)
        ,%s
        ,%s
    )
'''
FETCH_ENTRIES_START = '''
    SELECT
        members.full_name AS full_name
        ,entry_log.rfid AS rfid
        ,locations.name AS location
        ,entry_log.entry_time AS entry_time
        ,entry_log.is_active_tag AS is_active_tag
        ,entry_log.is_found_tag AS is_found_tag
    FROM entry_log
    LEFT OUTER JOIN members ON entry_log.rfid = members.rfid
    LEFT OUTER JOIN locations ON entry_log.location = locations.id
'''
FETCH_ENTRIES_WHERE_CLAUSE = '''
    WHERE entry_log.rfid = %s
'''
FETCH_ENTRIES_END = '''
    ORDER BY entry_log.entry_time DESC
    LIMIT %s
    OFFSET %s
'''

SET_MEMBER_ACTIVE_STATUS = '''
    UPDATE members
    SET active = %s
    WHERE rfid = %s
'''

EDIT_RFID_TAG = '''
    UPDATE members
    SET rfid = %s
    WHERE rfid = %s
'''

EDIT_NAME = '''
    UPDATE members
    SET full_name = %s
    WHERE rfid = %s
'''

DUMP_ACTIVE_MEMBERS = '''
    SELECT rfid FROM members WHERE active = True
'''
SQLITE_DUMP_ACTIVE_MEMBERS = '''
    SELECT rfid FROM members WHERE active = 1
'''

CASE_INSENSITIVE_NAME_SEARCH = '''
    full_name ILIKE %s
'''
LIMIT = '''
    LIMIT %s
'''
OFFSET = '''
    OFFSET %s
'''
PLACEHOLDER = '%s'

SET_MEMBER_PASSWORD = '''
    UPDATE members
    SET
        password_type = %s,
        encoded_password = %s
    WHERE rfid = %s
'''

GET_MEMBER_PASSWORD = '''
    SELECT
        password_type,
        encoded_password
    FROM members
    WHERE rfid = %s
    LIMIT 1
'''

DT_CONVERT_FUNC = None

IS_SQL_LITE = False



def _pg_datetime_convert( dt ):
    return dt.isoformat()

def _sqlite_datetime_convert( dt ):
    return dt

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
        'host=' + host,
        'port=' + str( port ),
        'connect_timeout=60',
    ])

    conn = psycopg2.connect( conn_str )
    conn.set_session( autocommit = True )
    return conn

def set_db( conn ):
    global CONN
    # Clear out any existing connection first
    CONN = None
    CONN = conn

def conn():
    return CONN

def close():
    CONN.close()

def set_sqlite():
    placeholder_change = re.compile( '%s' )

    # No, python does not have sensible variable scoping rules, why do you ask?
    global INSERT_MEMBER
    global FETCH_MEMBER_BY_NAME
    global FETCH_MEMBER_BY_RFID
    global LOG_ENTRY
    global FETCH_ENTRIES_START
    global FETCH_ENTRIES_WHERE_CLAUSE
    global FETCH_ENTRIES_END
    global SET_MEMBER_ACTIVE_STATUS
    global EDIT_RFID_TAG
    global EDIT_NAME
    global DUMP_ACTIVE_MEMBERS
    global CASE_INSENSITIVE_NAME_SEARCH
    global LIMIT
    global OFFSET
    global PLACEHOLDER
    global SET_MEMBER_PASSWORD
    global GET_MEMBER_PASSWORD
    global DT_CONVERT_FUNC
    global IS_SQL_LITE

    INSERT_MEMBER = re.sub( placeholder_change, '?', INSERT_MEMBER )
    FETCH_MEMBER_BY_NAME = re.sub( placeholder_change, '?',
        FETCH_MEMBER_BY_NAME )
    FETCH_MEMBER_BY_RFID = re.sub( placeholder_change, '?',
        FETCH_MEMBER_BY_RFID )
    LOG_ENTRY = re.sub( placeholder_change, '?', LOG_ENTRY )
    FETCH_ENTRIES_START = re.sub( placeholder_change, '?', FETCH_ENTRIES_START )
    FETCH_ENTRIES_WHERE_CLAUSE = re.sub( placeholder_change, '?',
        FETCH_ENTRIES_WHERE_CLAUSE )
    FETCH_ENTRIES_END = re.sub( placeholder_change, '?', FETCH_ENTRIES_END )
    SET_MEMBER_ACTIVE_STATUS = re.sub( placeholder_change, '?',
        SET_MEMBER_ACTIVE_STATUS )
    EDIT_RFID_TAG = re.sub( placeholder_change, '?',
        EDIT_RFID_TAG )
    EDIT_NAME = re.sub( placeholder_change, '?',
        EDIT_NAME )
    CASE_INSENSITIVE_NAME_SEARCH = re.sub( placeholder_change, '?',
        CASE_INSENSITIVE_NAME_SEARCH )
    LIMIT = re.sub( placeholder_change, '?', LIMIT )
    OFFSET = re.sub( placeholder_change, '?', OFFSET )
    SET_MEMBER_PASSWORD = re.sub( placeholder_change, '?',
        SET_MEMBER_PASSWORD )
    GET_MEMBER_PASSWORD = re.sub( placeholder_change, '?',
        GET_MEMBER_PASSWORD )

    # SQLite doesn't have ILIKE, so hack around it
    FETCH_MEMBER_BY_NAME = '''
        SELECT full_name, rfid, active, mms_id
        FROM members
        WHERE lower( full_name ) LIKE lower( ? )
    '''
    CASE_INSENSITIVE_NAME_SEARCH = 'lower( full_name ) LIKE lower( ? )'


    DUMP_ACTIVE_MEMBERS = SQLITE_DUMP_ACTIVE_MEMBERS
    PLACEHOLDER = '?'
    DT_CONVERT_FUNC = _sqlite_datetime_convert

    IS_SQL_LITE = True

def _run_statement(
    statement,
    args = None,
    _do_reconnect = 1,
):
    try:
        sql = conn()
        cur = sql.cursor()
        cur.execute( statement, args )
        return cur
    except BaseException as err:
        if (not IS_SQL_LITE) and sql.closed != 0:
            print( "Database closed on us, attempting to reconnect",
                file = sys.stderr )
            time.sleep( 1 )

            new_conn = db_connect()
            set_db( new_conn )

            time.sleep( 1 )
            return _run_statement( statement, args, 0 )
        else:
            raise


def add_member(
    name: str,
    rfid: str,
    mms_id: str = None,
):
    cur = _run_statement( INSERT_MEMBER, ( name, rfid, mms_id ) )
    cur.close()
    return

def change_tag(
    current_rfid: str,
    new_rfid: str,
):
    cur = _run_statement( EDIT_RFID_TAG, ( new_rfid, current_rfid ) )
    cur.close()
    return

def change_name(
    rfid: str,
    new_name: str,
):
    cur = _run_statement( EDIT_NAME, ( new_name, rfid ) )
    cur.close()
    return


def fetch_member_by_name(
    name: str,
):
    name = name + '%'

    cur = _run_statement( FETCH_MEMBER_BY_NAME, [ name ] )
    row = cur.fetchone()
    cur.close()

    if None == row:
        return None
    else:
        member = {
            'full_name': row[0],
            'rfid': row[1],
            'is_active': True if row[2] else False,
            'mms_id': row[3],
        }
        return member

def fetch_member_by_rfid(
    rfid: str,
):
    cur = _run_statement( FETCH_MEMBER_BY_RFID, [ rfid ] )
    row = cur.fetchone()
    cur.close()

    if None == row:
        return None
    else:
        member = {
            'id': row[0],
            'full_name': row[1],
            'rfid': row[2],
            'is_active': True if row[3] else False,
            'mms_id': row[4],
        }
        return member

def log_entry(
    rfid: str,
    location: str,
    is_active_tag: bool,
    is_found_tag: bool,
):
    cur = _run_statement( LOG_ENTRY, [
        rfid, location, is_active_tag, is_found_tag
    ] )
    cur.close()
    return

def _map_entry( entry ):
    result = {
        'full_name': entry[0],
        'rfid': entry[1],
        'location': entry[2],
        'entry_time': DT_CONVERT_FUNC( entry[3] ),
        'is_active_tag': True if entry[4] else False,
        'is_found_tag': True if entry[5] else False,
    }
    return result

def fetch_entries(
    limit: int = 100,
    offset: int = 0,
    tag: str = "",
):
    statement = FETCH_ENTRIES_START
    params = []
    if tag:
        statement += FETCH_ENTRIES_WHERE_CLAUSE
        params.append( tag )
    statement += FETCH_ENTRIES_END
    params.append( limit )
    params.append( offset )

    cur = _run_statement( statement, params )
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
    cur = _run_statement( SET_MEMBER_ACTIVE_STATUS, ( False, rfid ) )
    cur.close()
    return

def activate_member(
    rfid: str
):
    cur = _run_statement( SET_MEMBER_ACTIVE_STATUS, ( True, rfid ) )
    cur.close()
    return

def _map_search_members( entry ):
    result = {
        'rfid': entry[0],
        'full_name': entry[1],
        'active': True if entry[2] else False,
        'mms_id': entry[3],
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
        where.append( CASE_INSENSITIVE_NAME_SEARCH )
        params.append( '%' + full_name + '%' )

    if rfid:
        where.append( 'rfid = ' + PLACEHOLDER )
        params.append( rfid )

    if limit or offset:
        end.append( 'ORDER BY join_date' )

    if limit:
        end.append( LIMIT )
        params.append( limit )

    if offset:
        end.append( OFFSET )
        params.append( offset )



    statements = [
        'SELECT rfid, full_name, active, mms_id FROM members'
    ]
    if where:
        statements.append( 'WHERE' )
        statements.append( ' AND '.join( where ) )
    statements.append( ' '.join( end ) )
    statement = ' '.join( statements )

    cur = _run_statement( statement, params )
    rows = cur.fetchall()
    cur.close()

    results = map(
        _map_search_members,
        rows,
    )
    return list( results )

def dump_active_members():
    cur = _run_statement( DUMP_ACTIVE_MEMBERS, [] )

    results = {}
    for row in cur.fetchall():
        rfid = row[0]
        results[ rfid ] = True
    cur.close()

    return results

def set_password(
    rfid: str,
    password_plaintext: str,
    config: dict = {},
):
    password_type_full = _password_name( config )
    encoded_password = _encode_password( password_plaintext, config )

    cur = _run_statement( SET_MEMBER_PASSWORD, [
        password_type_full,
        encoded_password,
        rfid,
    ])
    cur.close()
    return

def _encode_password(
    password_plaintext: str,
    options: dict,
):
    password_type = options[ 'type' ]

    if PASSWORD_TYPE_PLAINTEXT == password_type:
        return password_plaintext
    elif PASSWORD_TYPE_BCRYPT == password_type:
        # SHA256 first so we never hit bcrypt's 72 char limit
        hashed_pass = base64.b64encode(
            hashlib.sha256( password_plaintext.encode( 'utf-8' ) ).digest()
        )
        encoded = bcrypt.hashpw(
            hashed_pass,
            bcrypt.gensalt( options[ 'bcrypt' ][ 'difficulty' ] ),
        )
        return encoded
    else:
        return password_plaintext

def auth_password(
    rfid: str,
    password_plaintext: str,
    config = {},
):
    cur = _run_statement( GET_MEMBER_PASSWORD, [
        rfid,
    ])
    row = cur.fetchone()
    cur.close()

    if None == row:
        return False
    else:
        password_type = row[0]
        password_encoded = row[1]
        matched = _match_password(
            password_type,
            password_plaintext,
            password_encoded,
        )

        # Reencode password if it's not our preferred encoding type
        if matched and not _is_preferred_auth( password_type, config ):
            set_password( rfid, password_plaintext, config )

        return matched

def _match_password(
    password_type: str,
    password_plaintext: str,
    password_encoded: str,
):
    if PASSWORD_TYPE_PLAINTEXT == password_type:
        # TODO Constant time matching algorithm. Or don't; it's not like 
        # plaintext passes should be used beyond testing, anyway.
        return password_plaintext == password_encoded
    elif re.match( r'^bcrypt_(\d+)$', password_type ):
        # SHA256 first so we never hit bcrypt's 72 char limit
        hashed_pass = base64.b64encode(
            hashlib.sha256( password_plaintext.encode( 'utf-8' ) ).digest()
        )
        return bcrypt.checkpw( hashed_pass, password_encoded )
    else:
        # Unknown type
        return False

def _password_name(
    options = {},
):
    password_type = options[ 'type' ]
    if PASSWORD_TYPE_PLAINTEXT == password_type:
        return "plaintext"
    elif PASSWORD_TYPE_BCRYPT == password_type:
        difficulty = options[ 'bcrypt' ][ 'difficulty' ]
        return "bcrypt_" + str( difficulty )
    else:
        return None

def _is_preferred_auth(
    password_type: str,
    config: dict = {},
):
    if password_type == config[ 'type' ]:
        return True
    elif m := re.match( r'^bcrypt_(\d+)$', password_type ):
        if (PASSWORD_TYPE_BCRYPT == password_type) and (
            m.group(1) == config[ 'bcrypt' ][ 'difficulty' ]
        ):
            return True
        else:
            return False
    return False


DT_CONVERT_FUNC = _pg_datetime_convert
