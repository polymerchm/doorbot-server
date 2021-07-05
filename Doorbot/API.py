import flask
import re
import Doorbot.DB as DB

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


app = flask.Flask( __name__ )


@app.route( "/check_tag/<tag>",  methods = [ "GET" ] )
def check_tag( tag ):
    response = flask.make_response()
    if not MATCH_INT.match( tag ):
        response.status = 400
        return response

    member = DB.fetch_member_by_rfid( tag )
    if None == member:
        response.status = 404
    elif member[ 'is_active' ]:
        response.status = 200
    else:
        response.status = 403

    return response

@app.route( "/entry/<tag>/<location>", methods = [ "GET" ] )
def log_entry( tag, location ):
    response = flask.make_response()
    if (not MATCH_INT.match( tag )) or (not MATCH_NAME.match( location )):
        response.status = 400
        return response

    member = DB.fetch_member_by_rfid( tag )
    if None == member:
        DB.log_entry( tag, location, False, False )
        response.status = 404
    elif member[ 'is_active' ]:
        DB.log_entry( tag, location, True, True )
        response.status = 200
    else:
        DB.log_entry( tag, location, False, True )
        response.status = 403

    return response
