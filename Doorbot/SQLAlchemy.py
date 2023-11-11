import base64
import bcrypt
import hashlib
import re
import Doorbot.Config
from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import Boolean, Date, DateTime, String
from sqlalchemy import create_engine
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


PASSWORD_TYPE_PLAINTEXT = "plaintext"
PASSWORD_TYPE_BCRYPT = "bcrypt"


__ENGINE = None

def __connect_pg():
    pg_conf = Doorbot.Config.get( 'postgresql' )
    user = pg_conf[ 'username' ]
    passwd = pg_conf[ 'passwd' ]
    database = pg_conf[ 'database' ]
    host = pg_conf[ 'host' ]
    port = pg_conf[ 'port' ]

    conn_str = "postgresql+psycopg2://" + \
        user + ":" + passwd + \
        "@" + host + ":" + str( port ) + \
        "/" + database

    engine = create_engine( conn_str )
    return engine

def set_engine_sqlite():
    global __ENGINE
    __ENGINE = create_engine( "sqlite://" )
    Base.metadata.create_all( __ENGINE )

def get_engine():
    global __ENGINE

    if __ENGINE is None:
        __ENGINE = __connect_pg()

    return __ENGINE


class Base( DeclarativeBase ):
    pass

class Member( Base ):
    __tablename__ = "members"

    id: Mapped[ int ] = mapped_column( primary_key = True )
    rfid: Mapped[ str ] = mapped_column( String() )
    active: Mapped[ bool ] = mapped_column(
        Boolean(),
        nullable = False,
        default = True,
    )
    mms_id: Mapped[ str ] = mapped_column(
        String(),
        nullable = True,
    )
    full_name: Mapped[ str ] = mapped_column(
        String(),
        nullable = False,
    )
    join_date: Mapped[ str ] = mapped_column(
        Date(),
        nullable = False,
        server_default = func.current_date(),
    )
    end_date: Mapped[ str ] = mapped_column(
        Date(),
        nullable = True,
    )
    phone: Mapped[ str ] = mapped_column(
        String(),
        nullable = False,
        default = '',
    )
    email: Mapped[ str ] = mapped_column(
        String(),
        nullable = False,
        default = '',
    )
    entry_type: Mapped[ str ] = mapped_column(
        String(),
        nullable = False,
        default = '',
    )
    notes: Mapped[ str ] = mapped_column(
        String(),
        nullable = True,
    )
    password_type: Mapped[ str ] = mapped_column(
        String(),
        nullable = True,
    )
    encoded_password: Mapped[ str ] = mapped_column(
        String(),
        nullable = True,
    )


    def set_password(
        self,
        password_plaintext,
        config: dict = {},
    ):
        password_type_full = self._password_name( config )
        encoded_password = self._encode_password( password_plaintext, config )
        self.password_type = password_type_full
        self.encoded_password = encoded_password
        return

    def _password_name(
        self,
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

    def _encode_password(
        self,
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
        self,
        rfid: str,
        password_plaintext: str,
        config = {},
    ):
        # TODO
        # * Find member
        # * Match password
        # * Re-encode password if it's not the preferred encryption type
        #
        return True

    def _match_password(
        self,
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



class Location( Base ):
    __tablename__ = "locations"

    id: Mapped[ int ] = mapped_column( primary_key = True )
    name: Mapped[ str ] = mapped_column(
        String(),
        nullable = False,
    )

    entries: Mapped[ List[ "EntryLog" ] ] = relationship(
        back_populates = "get_location",
    )

class EntryLog( Base ):
    __tablename__ = "entry_log"

    id: Mapped[ int ] = mapped_column( primary_key = True )
    rfid: Mapped[ str ] = mapped_column(
        String(),
        nullable = False,
    )
    entry_time: Mapped[ str ] = mapped_column(
        DateTime(),
        nullable = False,
        default = func.now(),
    )
    is_active_tag: Mapped[ bool ] = mapped_column(
        Boolean(),
        nullable = False,
    )
    is_found_tag: Mapped[ bool ] = mapped_column(
        Boolean(),
        nullable = False,
    )
    location: Mapped[ int ] = mapped_column(
        ForeignKey( "locations.id" )
    )

    get_location: Mapped[ "Location" ] = relationship(
        back_populates = "entries"
    )
