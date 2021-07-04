import flask
import re
import Doorbot.DB as DB

MATCH_INT = re.compile( ''.join([
    '^',
    '\\d+',
    '$',
]) )


app = flask.Flask( __name__ )


@app.route( "/check_tag/<tag>",  methods = [ "GET" ] )
def homepage( tag ):
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
