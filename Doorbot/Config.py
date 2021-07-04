from yaml import load, CLoader as Loader
import pathlib


CONF_FILE = "config.yml"
CONF = {}
INIT = False


def init(
    file_path: str = 'config.yml'
):
    cur_dir = pathlib \
        .Path( __file__ ) \
        .parent \
        .resolve()
    full_conf_path = pathlib \
        .PurePath( cur_dir, '..', file_path )

    yaml_input = pathlib.Path( full_conf_path ).read_text()
    global CONF
    CONF = load( yaml_input, Loader = Loader )

    INIT = True


def get(
    name: str
):
    if not INIT:
        init()
    return CONF[ name ]
