import fdb
import flask
# from models import BaseModel


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(flask.g, 'fb_db'):
        flask.g.fb_db = fdb.connect(
            dsn='db/TIMETABLE.FDB',
            user='SYSDBA',
            password='masterkey',
            connection_class=fdb.ConnectionWithSchema,
            charset='UTF8'
        )
    return flask.g.fb_db


def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(flask.g, 'fb_db'):
        flask.g.fb_db.close()


class BaseManager:
    def __init__(self, table_name):
        self.table_name = table_name

    def fetch_all(self):
        cur = get_db().cursor()
        cur.execute("SELECT * from " + self.table_name)
        return cur.fetchall()

