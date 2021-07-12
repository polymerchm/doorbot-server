import Doorbot.DB as DB

TABLES = [
    '''CREATE TABLE members (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        rfid TEXT NOT NULL UNIQUE,
        active BOOLEAN NOT NULL DEFAULT TRUE,
        full_name TEXT NOT NULL,
        join_date DATE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        end_date DATE,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        entry_type TEXT NOT NULL,
        notes TEXT
    )''',

    '''CREATE TABLE locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        name TEXT NOT NULL UNIQUE
    )''',

    '''CREATE TABLE entry_log (
        id              INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        -- This could be some random RFID tag, which we may not have in our 
        -- database.  So don't reference tags in bodgery_rfid directly.
        rfid            TEXT NOT NULL,
        entry_time      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        is_active_tag   BOOLEAN NOT NULL,
        is_found_tag    BOOLEAN NOT NULL,
        location        INT REFERENCES locations (id)
    )''',
    'CREATE INDEX entry_log_time_inx ON entry_log (entry_time DESC)',
    '''INSERT INTO locations (name) VALUES
        ( "cleanroom.door" )
        ,( "garage.door" )
        ,( "woodshop.door" )
        ,( "dummy" )''',
]


def create():
    conn = DB.conn()

    for sql in TABLES:
        conn.execute( sql )
