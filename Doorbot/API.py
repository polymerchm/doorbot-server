import flask
import os
import re
import Doorbot.Config
from Doorbot.SQLAlchemy import EntryLog, Location, Member, get_session
from sqlalchemy import select

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

    DB.deactivate_member( tag )
    response.status = 200
    return response

@app.route( "/secure/reactivate_tag/<tag>", methods = [ "POST" ] )
#@auth.login_required
def reactivate_tag( tag ):
    response = flask.make_response()
    if not MATCH_INT.match( tag ):
        response.status = 400
        return response

    DB.activate_member( tag )
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

    DB.change_tag( current_tag, new_tag )
    response.status = 201
    return response

@app.route( "/secure/edit_name/<tag>/<new_name>", methods = [ "POST" ] )
#@auth.login_required
def edit_name( tag, new_name ):
    response = flask.make_response()
    if not MATCH_INT.match( tag ):
        response.status = 400
        return response

    DB.change_name( tag, new_name )
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

    members = DB.search_members( name, tag, offset, limit )

    out = ''
    for member in members:
        out += ','.join([
            member[ 'rfid' ],
            member[ 'full_name' ],
            "1" if member[ 'active' ] else "0",
            member[ 'mms_id' ] if  member[ 'mms_id' ] else "",
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

    entries = DB.fetch_entries( limit, offset, tag )

    out = ''
    for entry in entries:
        out += ','.join([
            entry[ 'full_name' ] if entry[ 'full_name' ] else "",
            entry[ 'rfid' ],
            entry[ 'entry_time' ],
            "1" if entry[ 'is_active_tag' ] else "0",
            "1" if entry[ 'is_found_tag' ] else "0",
            entry[ 'location' ] if entry[ 'location' ] else "",
        ]) + "\n"

    response.status = 200
    response.content_type = 'text/plain'
    response.set_data( out )
    return response


@app.route( "/secure/dump_active_tags", methods = [ "GET" ] )
#@auth.login_required
def dump_tags():
    out = DB.dump_active_members()
    return out

#@app.route('/', defaults={'path': ''})
#@app.route( "/<path:path>" )
#def catch_all_secure( path ):
#    print( f'Hit catch all with {path}' )
#    return flask.send_from_directory( 'static', path )
