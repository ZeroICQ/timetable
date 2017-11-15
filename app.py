import fdb
import flask
from flask import Flask
from flask import request
from flask import render_template
import managers
import models

app = Flask(__name__)


@app.teardown_appcontext
def on_teardown(error):
    managers.close_db(error)


def get_models():
    tables = (
        models.AudienceModel,
    )
    return tables


# def get_tabled_headers(selected_table):
#     return [coll.name for coll in get_db().get_table(get_tables()[selected_table]).columns]


@app.route("/")
def index():
    data = {}
    tables = get_models()

    data['tables'] = tables

    selected_table = request.args.get('t', '')

    try:
        selected_table = int(selected_table)
    except ValueError:
        return render_template('list.html', **data)

    if 0 <= selected_table < len(tables):
        data['selected_table'] = selected_table

        selected_model = tables[selected_table]()

        #TODO: узнать насколько это плохо и как убрать циклическую зависимость иначе
        manager = getattr(managers, selected_model.get_manager())(selected_model)
        data['table_headers'] = selected_model.get_titles()
        data['entries'] = manager.fetch_all_raw()


    return render_template('list.html', **data)


# @app.route("/schedule")
# def schedule():
#     con = get_db()
#     cur = con.cursor()
#     data = {}
#     data['tables'] = get_tables()
#
#     cur.execute('''
#         SELECT
#             sc_it.id,
#             ls.name,
#             sub.name,
#             aud.name,
#             grp.name,
#             tch.name,
#             tps.name,
#             wkd.name
#         from SCHED_ITEMS sc_it
#         LEFT JOIN LESSONS ls on ls.id = sc_it.lesson_id
#         LEFT JOIN SUBJECTS sub on sub.id = sc_it.subject_id
#         LEFT JOIN AUDIENCES aud on aud.id = sc_it.audience_id
#         LEFT JOIN GROUPS grp on grp.id = sc_it.group_id
#         LEFT JOIN TEACHERS tch on tch.id = sc_it.teacher_id
#         LEFT JOIN LESSON_TYPES tps on tps.id = sc_it.type_id
#         LEFT JOIN WEEKDAYS wkd on wkd.id = sc_it.weekday_id
#         ''')
#     data['entries'] = cur.fetchall()
#     data['selected_table'] = 4
#     data['table_headers'] = ['ID', 'LESSON', 'SUBJECT', 'AUDIENCE', 'GROUPS', 'TEACHER', 'LESSON_TYPE', 'WEEKDAY']
#     return render_template('list.html', **data)
