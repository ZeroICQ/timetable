import fdb
from flask import Flask
from flask import request
from flask import render_template
from flask import g


app = Flask(__name__)


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'fb_db'):
        g.fb_db = fdb.connect(
            dsn='db/TIMETABLE.FDB',
            user='SYSDBA',
            password='masterkey',
            charset='UTF8'
        )
    return g.fb_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'fb_db'):
        g.fb_db.close()


def get_tables():
    cur = get_db().cursor()
    query = '''select 
                   rdb$relation_name 
               from 
                   rdb$relations 
               where rdb$view_blr is null 
                   and (rdb$system_flag is null or rdb$system_flag = 0)'''
    cur.execute(query);
    tables = tuple([x[0] for x in cur.fetchall()])
    return tables


@app.route("/")
def index():
    cur = get_db().cursor()
    query = 'SELECT * FROM WEEKDAYS';
    cur.execute(query);
    return render_template('list.html', tables=get_tables(), entries=cur.fetchall())

