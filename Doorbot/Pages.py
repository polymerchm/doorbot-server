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

@app.route( "/login", methods = [ "GET" ] )
def login_form():
    return render_template( 'login', page_name = "Login" )

@app.route( "/login", methods = [ "POST" ] )
def login():
    request = flask.request
    tag = request.form[ 'username' ]
    password = request.form[ 'password' ]

    session = get_session()
    member = Member.get_by_tag( tag, session )

    response = flask.make_response()
    if not member:
        return error_page(
            response,
            "Incorrect Login",
            tmpl = "login",
            page_name = "Login",
            status = 404,
        )
    elif not member.check_password( password ):
        return error_page(
            response,
            "Incorrect Login",
            tmpl = "login",
            page_name = "Login",
            status = 404,
        )
    else:
        flask.session[ 'rfid' ] = tag
        return flask.redirect( '/secure/index.html', code = 301 )
