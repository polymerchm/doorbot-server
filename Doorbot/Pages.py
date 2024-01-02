import Doorbot.Config
import flask
from Doorbot.API import app
from Doorbot.SQLAlchemy import Location
from Doorbot.SQLAlchemy import EntryLog
from Doorbot.SQLAlchemy import Member
from Doorbot.SQLAlchemy import Permission
from Doorbot.SQLAlchemy import Role
from Doorbot.SQLAlchemy import get_engine
from Doorbot.SQLAlchemy import get_session
from datetime import datetime
from flask_stache import render_template
from sqlalchemy import select
from sqlalchemy.sql import text


def error_page(
    response,
    tmpl,
    msgs = [],
    status = 500,
    page_name = "",
    username = None,
):
    output = render_template(
        tmpl,
        page_name = page_name,
        username = username,
        has_errors = True,
        errors = msgs,
    )

    response.status = status
    response.set_data( output )
    return response

def require_logged_in( func ):
    def check():
        if flask.session.get( 'username' ) is None:
            return login_form([ "You must be logged in to access this page" ])
        else:
            return func()

    # Avoid error of "View function mapping is overwriting an existing endpoint 
    # function"
    check.__name__ = func.__name__

    return check

@app.route( "/home", methods = [ "GET" ] )
@require_logged_in
def home_page():
    username = flask.session.get( 'username' )

    return render_template(
        'home',
        page_name = "Home",
        username = username,
    )

@app.route( "/login", methods = [ "GET" ] )
def login_form( errors = [] ):
    has_error = True if errors else False

    return render_template(
        'login',
        page_name = "Login",
        has_errors = has_error,
        errors = errors,
    )

@app.route( "/login", methods = [ "POST" ] )
def login():
    request = flask.request
    username = request.form[ 'username' ]
    password = request.form[ 'password' ]

    session = get_session()
    member = Member.get_by_username( username, session )

    response = flask.make_response()
    if not member:
        return error_page(
            response,
            msgs = [ "Incorrect Login" ],
            tmpl = "login",
            page_name = "Login",
            status = 404,
        )
    elif not member.check_password( password, session ):
        return error_page(
            response,
            msgs = [ "Incorrect Login" ],
            tmpl = "login",
            page_name = "Login",
            status = 404,
        )
    else:
        flask.session[ 'username' ] = username
        return home_page()

@app.route( "/logout" )
def logout():
    flask.session[ 'username' ] = None
    return login_form([ "You have been logged out" ])

@app.route( "/add-tag", methods = [ "GET" ] )
@require_logged_in
def add_tag_form():
    username = flask.session.get( 'username' )

    return render_template(
        'add_tag',
        page_name = "Add RFID Tag",
        username = username,
    )

@app.route( "/add-tag", methods = [ "POST" ] )
@require_logged_in
def add_tag():
    username = flask.session.get( 'username' )

    request = flask.request
    rfid = request.form[ 'rfid' ]
    name = request.form[ 'name' ]

    session = get_session()

    errors = []
    if not Doorbot.API.MATCH_INT.match( rfid ):
        errors.append( "RFID should be an series of digits" )
    if not Doorbot.API.MATCH_NAME.match( name ):
        errors.append( "Member Name should be a string" )

    if not errors:
        member = Member.get_by_tag( rfid, session )
        if not member is None:
            errors.append( "Member with RFID tag " + rfid + " already exists" )

    response = flask.make_response()
    if errors:
        return error_page(
            response,
            msgs = errors,
            tmpl = "add_tag",
            page_name = "Add RFID Tag",
            status = 400,
            username = username,
        )
    else:
        member = Member(
            full_name = name,
            rfid = rfid,
        )
        session.add( member )
        session.commit()

        return render_template(
            'add_tag',
            page_name = "Add RFID Tag",
            username = username,
            msg = "Added tag",
        )

@app.route( "/search-scan-logs", methods = [ "GET" ] )
@require_logged_in
def search_scan_logs():
    args = flask.request.args
    rfid = args.get( 'rfid' )
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

    logs = Doorbot.API.search_scan_logs( rfid, offset, limit )

    username = flask.session.get( 'username' )
    return render_template(
        'search_scan_logs',
        page_name = "Search Scan Logs",
        tags = logs,
        username = username,
    )

@app.route( "/view-tag-list", methods = [ "GET" ] )
@require_logged_in
def view_tag_list():
    args = flask.request.args
    name = args.get( 'search_name' )
    rfid = args.get( 'search_rfid' )
    offset = args.get( 'offset' )
    limit = args.get( 'limit' )

    # Normalize the data
    name = "" if name is None else name
    rfid = "" if rfid is None else rfid

    offset = int( offset ) if offset else 0
    limit = int( limit ) if limit else 0

    # Clamp offset/limit
    if offset < 0:
        offset = 0
    if limit < 0:
        limit = 50
    elif limit < 1:
        limit = 100
    elif limit > 100:
        limit = 100

    next_offset = offset + limit

    members = Doorbot.API.search_tag_list( name, rfid, offset, limit )
    formatted_members = list( map(
        lambda member: {
            "full_name": member.full_name,
            "tag": member.rfid,
            "is_active": member.active,
            "mms_id": member.mms_id if member.mms_id else "",
        },
        members,
    ))

    username = flask.session.get( 'username' )
    return render_template(
        'view_tag_list',
        page_name = "Search Tag List",
        tags = formatted_members,
        username = username,
        next_offset = next_offset,
        limit = limit,
        search_name = name,
        rfid = rfid,
    )

@app.route( "/edit-tag", methods = [ "GET" ] )
@require_logged_in
def edit_tag_form():
    username = flask.session.get( 'username' )

    current_tag = flask.request.args.get( 'current_tag' )
    current_tag = current_tag if current_tag else ''

    return render_template(
        'edit_tag',
        page_name = "Edit Tag",
        username = username,
        current_tag = current_tag,
    )

@app.route( "/edit-tag", methods = [ "POST" ] )
@require_logged_in
def edit_tag_submit():
    username = flask.session.get( 'username' )

    current_tag = flask.request.form[ 'current_tag' ]
    new_tag = flask.request.form[ 'new_tag' ]

    errors = []
    if not Doorbot.API.MATCH_INT.match( current_tag ):
        errors.append( "Current tag should be a series of digits" )
    if not Doorbot.API.MATCH_INT.match( new_tag ):
        errors.append( "New tag should be a series of digits" )

    response = flask.make_response()
    if errors:
        return error_page(
            response,
            tmpl = 'edit_tag',
            msgs = errors,
            status = 400,
            page_name = "Edit Tag",
            username = username,
        )

    session = get_session()
    member = Member.get_by_tag( current_tag, session )

    if not member:
        return error_page(
            response,
            tmpl = 'edit_tag',
            msgs = [ "Cannot find member for RFID " + current_tag ],
            status = 400,
            page_name = "Edit Tag",
            username = username,
        )

    member.rfid = new_tag
    session.add( member )
    session.commit()

    return render_template(
        'edit_tag',
        page_name = "Edit Tag",
        username = username,
        current_tag = new_tag,
        msg = "Changed RFID tag",
    )

@app.route( "/edit-name", methods = [ "GET" ] )
@require_logged_in
def edit_name_form():
    username = flask.session.get( 'username' )

    current_tag = flask.request.args.get( 'current_tag' )
    current_name = flask.request.args.get( 'current_name' )

    return render_template(
        'edit_name',
        page_name = "Edit Name",
        username = username,
        current_tag = current_tag,
        full_name = current_name
    )

@app.route( "/edit-name", methods = [ "POST" ] )
@require_logged_in
def edit_name_submit():
    username = flask.session.get( 'username' )

    current_tag = flask.request.form[ 'current_tag' ]
    new_name = flask.request.form[ 'new_name' ]

    errors = []
    if not Doorbot.API.MATCH_INT.match( current_tag ):
        errors.append( "Current tag should be a series of digits" )
    if not Doorbot.API.MATCH_NAME.match( new_name ):
        errors.append( "New name should be a string" )

    response = flask.make_response()
    if errors:
        return error_page(
            response,
            tmpl = 'edit_name',
            msgs = errors,
            status = 400,
            page_name = "Edit Name",
            username = username,
        )

    session = get_session()
    member = Member.get_by_tag( current_tag, session )

    if not member:
        return error_page(
            response,
            tmpl = 'edit_name',
            msgs = [ "Cannot find member for RFID " + current_tag ],
            status = 400,
            page_name = "Edit Name",
            username = username,
        )

    member.full_name = new_name
    session.add( member )
    session.commit()

    return render_template(
        'edit_name',
        page_name = "Edit Name",
        username = username,
        current_tag = current_tag,
        full_name = new_name,
        msg = "Changed member name",
    )

@app.route( "/activate-tag", methods = [ "POST" ] )
@require_logged_in
def activate_tag_submit():
    username = flask.session.get( 'username' )

    tag = flask.request.form[ 'tag' ]
    activate = int( flask.request.form[ 'activate' ] )

    page_name = "Activate Tag" if activate else "Deactivate Tag"

    errors = []
    if not Doorbot.API.MATCH_INT.match( tag ):
        errors.append( "Tag should be a series of digits" )

    response = flask.make_response()
    if errors:
        return error_page(
            response,
            tmpl = 'activate_tag',
            msgs = errors,
            status = 400,
            page_name = page_name,
            username = username,
        )

    session = get_session()
    member = Member.get_by_tag( tag, session )

    if not member:
        return error_page(
            response,
            tmpl = 'activate_tag',
            msgs = [ "Cannot find member for RFID " + current_tag ],
            status = 400,
            page_name = page_name,
            username = username,
        )

    member.active = True if activate else False
    session.add( member )
    session.commit()

    action = "Activated tag" if activate else "Deactivated tag"
    action = action + " " + tag + " for " + member.full_name

    return render_template(
        'activate_tag',
        page_name = page_name,
        username = username,
        msg = action,
    )
