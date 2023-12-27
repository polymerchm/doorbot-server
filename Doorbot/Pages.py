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
    msg,
    tmpl,
    status = 500,
    page_name = "",
):
    output = render_template(
        tmpl,
        page_name = page_name,
        has_errors = True,
        errors = [
            msg,
        ],
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
            "Incorrect Login",
            tmpl = "login",
            page_name = "Login",
            status = 404,
        )
    elif not member.check_password( password, session ):
        return error_page(
            response,
            "Incorrect Login",
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
