import base64
import bcrypt
import hashlib
import re
import Doorbot.Config
from typing import List
from typing import Optional
from sqlalchemy import Column
from sqlalchemy import Table
from sqlalchemy import ForeignKey
from sqlalchemy import Boolean, Date, DateTime, String
from sqlalchemy import create_engine
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session


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

def get_session():
    engine = get_engine()
    session = Session( engine )
    return session


class Base( DeclarativeBase ):
    pass

member_role_association = Table(
    "role_members",
    Base.metadata,
    Column( "member_id", ForeignKey( "members.id" ), primary_key = True ),
    Column( "role_id", ForeignKey( "roles.id" ), primary_key = True ),
)

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

    roles: Mapped[ List[ "Role" ] ] = relationship(
        "Role",
        secondary = lambda: member_role_association,
        back_populates = "members",
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
        options: dict = {},
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

    def check_password(
        self,
        password_plaintext: str,
    ):
        if self._password_does_match( password_plaintext ):
            target_config = Doorbot.Config.get( 'password_storage' )
            current_config = self._password_current_config()

            # Might be encrypted with an old way of doing things. Check the 
            # config, and if it's not the preferred type, then fix that.
            if not self._password_config_does_match(
                current_config,
                target_config,
            ):
                self.set_password(
                    password_plaintext,
                    target_config,
                )

            return True

        return False

    def _password_current_config( self ):
        password_config_str = self.password_type
        password_config = password_config_str.split( "_" )

        if PASSWORD_TYPE_PLAINTEXT == password_config[0]:
            return {
                "type": PASSWORD_TYPE_PLAINTEXT,
            }
        elif PASSWORD_TYPE_BCRYPT == password_config[0]:
            return {
                "type": PASSWORD_TYPE_BCRYPT,
                "bcrypt": {
                    "difficulty": int( password_config[1] ),
                },
            }
        else:
            # I dunno what it is. Return plaintext as default.
            return {
                "type": PASSWORD_TYPE_PLAINTEXT,
            }

    def _password_config_does_match(
        self,
        current_config,
        target_config,
    ):
        if current_config[ "type" ] == target_config[ "type" ]:
            if PASSWORD_TYPE_BCRYPT == target_config[ "type" ]:
                if current_config[ "bcrypt" ][ "difficulty" ] == target_config[ "bcrypt" ][ "difficulty" ]:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False


    def _password_does_match(
        self,
        password_plaintext: str,
    ):
        password_type = self.password_type
        password_encoded = self.encoded_password

        # Encoding must be normalized
        if not isinstance( password_encoded, bytes ):
            password_encoded = password_encoded.encode( 'utf-8' )
        if not isinstance( password_plaintext, bytes ):
            password_plaintext = password_plaintext.encode( 'utf-8' )

        if PASSWORD_TYPE_PLAINTEXT == password_type:
            # TODO Constant time matching algorithm. Or don't; it's not like 
            # plaintext passes should be used beyond testing, anyway.
            return password_plaintext == password_encoded
        elif re.match( r'^bcrypt_(\d+)$', password_type ):
            # SHA256 first so we never hit bcrypt's 72 char limit
            hashed_pass = base64.b64encode(
                hashlib.sha256( password_plaintext ).digest()
            )
            return bcrypt.checkpw( hashed_pass, password_encoded )
        else:
            # I dunno what it is. Assume it's wrong.
            return False

class Location( Base ):
    __tablename__ = "locations"

    id: Mapped[ int ] = mapped_column( primary_key = True )
    name: Mapped[ str ] = mapped_column(
        String(),
        nullable = False,
    )

    entries: Mapped[ List[ "EntryLog" ] ] = relationship(
        back_populates = "mapped_location",
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
        ForeignKey( "locations.id" ),
        nullable = True,
    )

    mapped_location: Mapped[ "Location" ] = relationship(
        back_populates = "entries"
    )

role_permission_association = Table(
    "role_permissions",
    Base.metadata,
    Column( "role_id", ForeignKey( "roles.id" ), primary_key = True ),
    Column( "permission_id", ForeignKey( "permissions.id" ), primary_key = True ),
)

class Role( Base ):
    __tablename__ = "roles"

    id: Mapped[ int ] = mapped_column( primary_key = True )
    name: Mapped[ str ] = mapped_column(
        String(),
        nullable = False,
    )

    permissions: Mapped[ List[ "Permission" ] ] = relationship(
        "Permission",
        secondary = lambda: role_permission_association,
        back_populates = "roles",
    )

    members: Mapped[ List[ "Member" ] ] = relationship(
        "Member",
        secondary = lambda: member_role_association,
        back_populates = "roles",
    )

    def has_permission( self, permission ):
        session = get_session()

        if isinstance( permission, Permission ):
            permission = permission.name
            stmt = select( Permission ).where(
                Permission.name == permission
            )
            permission = session.scalars( stmt ).one()

        result = session.query(
                Permission.name
            ).filter(
                role_permission_association.c.role_id == self.id,
            ).filter(
                role_permission_association.c.permission_id == Permission.id
            ).filter(
                Permission.name == permission
            ).first()

        return result is not None

class RoleUser( Base ):
    __tablename__ = "role_users"

    id: Mapped[ int ] = mapped_column( primary_key = True )
    member_id: Mapped[ int ] = mapped_column(
        ForeignKey( "members.id" ),
        nullable = False,
    )
    role_id: Mapped[ int ] = mapped_column(
        ForeignKey( "roles.id" ),
        nullable = False,
    )

class Permission( Base ):
    __tablename__ = "permissions"

    id: Mapped[ int ] = mapped_column( primary_key = True )
    name: Mapped[ str ] = mapped_column(
        String(),
        nullable = False,
    )

    roles: Mapped[ List[ "Role" ] ] = relationship(
        "Role",
        secondary = lambda: role_permission_association,
        back_populates = "permissions"
    )
