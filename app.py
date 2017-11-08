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
            connection_class=fdb.ConnectionWithSchema,
            charset='UTF8'
        )
    return g.fb_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'fb_db'):
        g.fb_db.close()


def get_tables():
    tables = (
            'AUDIENCES',
            'GROUPS',
            'LESSONS',
            'LESSON_TYPES',
            'SCHED_ITEMS',
            'SUBJECTS',
            'SUBJECT_GROUP',
            'SUBJECT_TEACHER',
            'TEACHERS',
            'WEEKDAYS',
            )
    return tables


def get_tabled_headers(selected_table):
    return [coll.name for coll in get_db().get_table(get_tables()[selected_table]).columns]


@app.route("/")
def index():
    con = get_db()
    cur = con.cursor()

    data = {}
    tables = get_tables()
    data['tables'] = tables

    selected_table = request.args.get('t', '')
    if (selected_table.isdigit() and
        int(selected_table) >= 0 and
        int(selected_table) < len(tables)):

        selected_table = int(selected_table)

        data['selected_table'] = selected_table
        data['table_headers'] = get_tabled_headers(selected_table)

        cur.execute("SELECT * from " + tables[selected_table])
        data['entries'] = cur.fetchall()

    return render_template('list.html', **data)

@app.route("/schedule")
def schedule():
    con = get_db()
    cur = con.cursor()
    data = {}
    data['tables'] = get_tables()

    cur.execute('''
        SELECT
            sc_it.id,
            ls.name,
            sub.name,
            aud.name,
            grp.name,
            tch.name,
            tps.name,
            wkd.name
        from SCHED_ITEMS sc_it
        LEFT JOIN LESSONS ls on ls.id = sc_it.lesson_id
        LEFT JOIN SUBJECTS sub on sub.id = sc_it.subject_id
        LEFT JOIN AUDIENCES aud on aud.id = sc_it.audience_id
        LEFT JOIN GROUPS grp on grp.id = sc_it.group_id
        LEFT JOIN TEACHERS tch on tch.id = sc_it.teacher_id
        LEFT JOIN LESSON_TYPES tps on tps.id = sc_it.type_id
        LEFT JOIN WEEKDAYS wkd on wkd.id = sc_it.weekday_id
        ''')
    data['entries'] = cur.fetchall()
    data['selected_table'] = 4
    return render_template('list.html', **data)
