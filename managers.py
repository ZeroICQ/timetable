import fdb
import flask
from models import BaseModel


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
    def __init__(self, model: BaseModel):
        self.model = model

    def fetch_all_raw(self):
        cur = get_db().cursor()
        table_name = self.model.get_table_name()

        colls = self.model.get_colls()
        last = len(colls) - 1

        sql = 'SELECT '
        for i, coll in enumerate(self.model.get_colls()):
            sql += coll.select_coll()
            if i != last:
                sql += ','
            sql += ' '

        sql += 'from ' + table_name
        cur.execute(sql)

        return cur.fetchall()

