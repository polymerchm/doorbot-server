import Doorbot.Config
from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import Boolean, Date, String
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


def __connect():
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
engine = __connect()

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
    mms_id: Mapped[ str ] = mapped_column( String() )
    full_name: Mapped[ str ] = mapped_column(
        String(),
        nullable = False,
    )
    join_date: Mapped[ str ] = mapped_column(
        Date(),
        nullable = False,
        default = 'NOW()'
    )
    end_date: Mapped[ str ] = mapped_column(
        Date(),
        nullable = True,
    )
    phone: Mapped[ str ] = mapped_column(
        String(),
        nullable = False,
    )
    email: Mapped[ str ] = mapped_column(
        String(),
        nullable = False,
    )
    entry_type: Mapped[ str ] = mapped_column(
        String(),
        nullable = False,
    )
    notes: Mapped[ str ] = mapped_column( String() )
    password_type: Mapped[ str ] = mapped_column( String() )
    encoded_password: Mapped[ str ] = mapped_column( String() )
