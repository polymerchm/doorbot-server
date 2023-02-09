-- For searching text fields with a good index
CREATE EXTENSION pg_trgm;

CREATE TABLE members (
    id SERIAL PRIMARY KEY NOT NULL,
    rfid TEXT UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    mms_id TEXT UNIQUE,
    full_name TEXT NOT NULL,
    join_date DATE NOT NULL DEFAULT NOW(),
    end_date DATE,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    entry_type TEXT NOT NULL,
    notes TEXT,
    password_type TEXT,
    encoded_password TEXT
);
CREATE INDEX members_full_name_trgm_idx ON members
    USING gist (full_name gist_trgm_ops);

CREATE TABLE locations (
    id SERIAL PRIMARY KEY NOT NULL,
    name TEXT NOT NULL UNIQUE
);
INSERT INTO locations (name) VALUES
    ( 'cleanroom.door' )
    ,( 'garage.door' )
    ,( 'woodshop.door' )
    ,( 'dummy' );

CREATE TABLE entry_log (
    id              SERIAL PRIMARY KEY NOT NULL,
    -- This could be some random RFID tag, which we may not have in our 
    -- database.  So don't reference tags in bodgery_rfid directly.
    rfid            TEXT NOT NULL,
    entry_time      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active_tag   BOOLEAN NOT NULL,
    is_found_tag    BOOLEAN NOT NULL,
    location        INT REFERENCES locations (id)
);
CREATE INDEX ON entry_log (entry_time DESC);
