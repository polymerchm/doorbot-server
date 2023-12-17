import flask
import os
import re
import Doorbot.Config
from Doorbot.SQLAlchemy import Location
from Doorbot.SQLAlchemy import EntryLog
from Doorbot.SQLAlchemy import Member
from Doorbot.SQLAlchemy import get_engine
from Doorbot.SQLAlchemy import get_session
from sqlalchemy import select
from sqlalchemy.sql import text

MATCH_INT = re.compile( ''.join([
    '^',
    '\\d+',
    '$',
]) )
MATCH_NAME = re.compile( ''.join([
    '^',
    '[',
        '\\w',
        '\\s',
        '\\-',
        '\\.',
    ']+',
    '$',
]) )


app = flask.Flask( __name__,
    static_url_path = '',
    static_folder = '../static',
)


@app.route( "/" )
@app.route( "/index.html" )
def redirect_home():
    return flask.redirect( '/secure/index.html', code = 301 )

@app.route( "/check_tag/<tag>",  methods = [ "GET" ] )
#@auth.login_required
def check_tag( tag ):
    response = flask.make_response()
    if not MATCH_INT.match( tag ):
        response.status = 400
        return response

    session = get_session()
    stmt = select( Member ).where(
        Member.rfid == tag
    )
    member = session.scalars( stmt ).one_or_none()

    if None == member:
        response.status = 404
    elif member.active:
        response.status = 200
    else:
        response.status = 403

    return response

@app.route( "/entry/<tag>/<location>", methods = [ "GET" ] )
#@auth.login_required
def log_entry( tag, location ):
    response = flask.make_response()
    if (not MATCH_INT.match( tag )) or (not MATCH_NAME.match( location )):
        response.status = 400
        return response

    session = get_session()
    stmt = select( Member ).where(
        Member.rfid == tag
    )
    member = session.scalars( stmt ).one_or_none()

    stmt = select( Location ).where(
        Location.name == location
    )
    location_db = session.scalars( stmt ).one()

    entry = EntryLog(
        rfid = tag,
        mapped_location = location_db,
    )

    if None == member:
        entry.is_active_tag = False
        entry.is_found_tag = False
        response.status = 404
    elif member.active:
        entry.is_active_tag = True
        entry.is_found_tag = True
        response.status = 200
    else:
        entry.is_active_tag = False
        entry.is_found_tag = True
        response.status = 403

    session.add( entry )
    session.add( location_db )
    session.commit()

    return response

@app.route( "/secure/new_tag/<tag>/<full_name>", methods = [ "PUT" ] )
#@auth.login_required
def new_tag( tag, full_name ):
    response = flask.make_response()
    if (not MATCH_INT.match( tag )) or (not MATCH_NAME.match( full_name )):
        response.status = 400
        return response

    session = get_session()
    member = Doorbot.SQLAlchemy.Member(
        full_name = full_name,
        rfid = tag,
    )
    session.add( member )
    session.commit()

    response.status = 201
    return response

@app.route( "/secure/deactivate_tag/<tag>", methods = [ "POST" ] )
#@auth.login_required
def deactivate_tag( tag ):
    response = flask.make_response()
    if not MATCH_INT.match( tag ):
        response.status = 400
        return response

    session = get_session()
    stmt = select( Member ).where(
        Member.rfid == tag
    )
    member = session.scalars( stmt ).one_or_none()

    member.active = False
    session.add( member )
    session.commit()

    response.status = 200
    return response

@app.route( "/secure/reactivate_tag/<tag>", methods = [ "POST" ] )
#@auth.login_required
def reactivate_tag( tag ):
    response = flask.make_response()
    if not MATCH_INT.match( tag ):
        response.status = 400
        return response

    session = get_session()
    stmt = select( Member ).where(
        Member.rfid == tag
    )
    member = session.scalars( stmt ).one_or_none()

    member.active = True
    session.add( member )
    session.commit()

    response.status = 200
    return response

@app.route( "/secure/edit_tag/<current_tag>/<new_tag>", methods = [ "POST" ] )
#@auth.login_required
def edit_tag( current_tag, new_tag ):
    response = flask.make_response()
    if not MATCH_INT.match( current_tag ):
        response.status = 400
        return response
    if not MATCH_INT.match( new_tag ):
        response.status = 400
        return response

    session = get_session()
    stmt = select( Member ).where(
        Member.rfid == current_tag
    )
    member = session.scalars( stmt ).one_or_none()

    member.rfid = new_tag
    session.add( member )
    session.commit()

    response.status = 201
    return response

@app.route( "/secure/edit_name/<tag>/<new_name>", methods = [ "POST" ] )
#@auth.login_required
def edit_name( tag, new_name ):
    response = flask.make_response()
    if not MATCH_INT.match( tag ):
        response.status = 400
        return response

    session = get_session()
    stmt = select( Member ).where(
        Member.rfid == tag
    )
    member = session.scalars( stmt ).one_or_none()

    member.full_name = new_name
    session.add( member )
    session.commit()

    response.status = 201
    return response


@app.route( "/secure/search_tags", methods = [ "GET" ] )
#@auth.login_required
def search_tags():
    args = flask.request.args
    response = flask.make_response()

    name = args.get( 'name' )
    tag = args.get( 'tag' )
    offset = args.get( 'offset' )
    limit = args.get( 'limit' )

    offset = int( offset ) if offset else 0
    limit = int( limit ) if limit else 0

    # Clamp offset/limit
    if offset < 0:
        offset = 0
    if limit < 0:
        limit = 50
    elif limit > 100:
        limit = 100

    stmt = select( Member )
    if name:
        stmt = stmt.where(
            Member.full_name.ilike( '%' + name + '%' )
        )
    if tag:
        stmt = stmt.where(
            Member.rfid == tag,
        )

    stmt = stmt.order_by(
        'join_date'
    ).limit(
        limit
    ).offset(
        offset
    )

    session = get_session()
    members = session.scalars( stmt ).all()

    out = ''
    for member in members:
        out += ','.join([
            member.rfid,
            member.full_name,
            "1" if member.active else "0",
            member.mms_id if member.mms_id else "",
        ]) + "\n"

    response.status = 200
    response.content_type = 'text/plain'
    response.set_data( out )
    return response

@app.route( "/secure/search_entry_log", methods = [ "GET" ] )
#@auth.login_required
def search_entry_log():
    args = flask.request.args
    response = flask.make_response()

    tag = args.get( 'tag' )
    offset = args.get( 'offset' )
    limit = args.get( 'limit' )

    offset = int( offset ) if offset else 0
    limit = int( limit ) if limit else 0

    # Clamp offset/limit
    if offset < 0:
        offset = 0
    if limit <= 0:
        limit = 50
    elif limit > 100:
        limit = 100

    # People could scan an RFID that isn't in the system. We still want to 
    # log that, but it means we can't explicitly link the member and entry_log 
    # tables. This is a problem for SQLAlchemy, so don't bother, and use raw 
    # SQL.
    sql_params = {
        "rfid": tag,
        "offset": offset,
        "limit": limit,
    }
    conn = get_engine().connect()
    stmt = text( """
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
        WHERE entry_log.rfid = :rfid
        ORDER BY entry_log.entry_time DESC
        LIMIT :limit
        OFFSET :offset
    """ )

    logs = conn.execute( stmt, sql_params )

    out = ''
    for entry in logs:
        out += ','.join([
            entry[ 0 ] if entry[ 0 ] else "",
            entry[ 1 ],
            entry[ 3 ],
            "1" if entry[ 4 ] else "0",
            "1" if entry[ 5 ] else "0",
            entry[ 2 ] if entry[ 2 ] else "",
        ]) + "\n"

    response.status = 200
    response.content_type = 'text/plain'
    response.set_data( out )
    return response

@app.route( "/secure/dump_active_tags/<permission>", methods = [ "GET" ] )
#@auth.login_required
def dump_tags_for_permission( permission ):
    session = get_session()
    stmt = select( Doorbot.SQLAlchemy.Permission ).where(
        Doorbot.SQLAlchemy.Permission.name == permission
    )
    found_permission = session.scalars( stmt ).one_or_none()

    response = flask.make_response()
    if found_permission is None:
        response.status = 404
        response.content_type = 'text/plain'
        response.set_data( "Permission " + permission + " was not found" )
        # TODO follow ErrorResponse definition in openapi
    else:
        members = {}
        for member in found_permission.all_members_with_permission():
            rfid = member.rfid
            members[ rfid ] = True

        json_data = flask.json.dumps( members )
        response.content_type = 'application/json'
        response.set_data( json_data )

    return response

@app.route( "/secure/dump_active_tags", methods = [ "GET" ] )
#@auth.login_required
def dump_tags():
    session = get_session()
    stmt = select( Member ).where(
        Member.active == True
    )
    members = session.scalars( stmt ).all()

    out = {}
    for member in members:
        rfid = member.rfid
        out[ rfid ] = True

    return out


@app.route( "/secure/change_passwd/<rfid>", methods = [ "PUT" ] )
#@auth.login_required
def change_password( rfid ):
    session = get_session()
    stmt = select( Member ).where(
        Member.rfid == rfid
    )
    member = session.scalars( stmt ).one_or_none()

    response = flask.make_response()

    if member is None:
        response.status = 404
        response.content_type = 'text/plain'
        response.set_data( "Member with RFID " + rfid + " was not found" )
        # TODO follow ErrorResponse definition in openapi
    else:
        pass1 = flask.request.form[ 'new_pass' ]
        pass2 = flask.request.form[ 'new_pass2' ]

        if pass1 != pass2:
            response.status = 400
            response.content_type = 'text/plain'
            response.set_data( "Passwords do not match" )
            # TODO follow ErrorResponse definition in openapi
        else:
            member.set_password( pass1, {
                "type": "plaintext",
            })
            response.status = 200

    return response

# TODO /secure/chagne_passwd
# TODO modify below TODOs to match evolved role/permission system
# TODO /secure/add_access/<rfid>/<permission>
# TODO /secure/remove_access/<rfid>/<permission>

#@app.route('/', defaults={'path': ''})
#@app.route( "/<path:path>" )
#def catch_all_secure( path ):
#    print( f'Hit catch all with {path}' )
#    return flask.send_from_directory( 'static', path )
