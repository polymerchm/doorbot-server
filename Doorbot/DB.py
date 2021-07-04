import psycopg2
import sqlite3

CONN = None

def set_db( conn ):
    global CONN
    CONN = conn
