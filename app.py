import fdb
import flask
from flask import Flask
from flask import request
from flask import render_template
import models
import misc

app = Flask(__name__)


@app.teardown_appcontext
def on_teardown(error):
    models.close_db(error)


def get_tables():
    tables = (
        models.AudienceModel,
        models.GroupsModel,
        models.LessonsModel,
        models.LessonTypesModel,
        models.SchedItemsModel,
        models.SubjectsModel,
        models.SubjectGroupModel,
        models.SubjectTeacherModel,
        models.TeachersModel,
        models.WeekdaysModel)
    return tables

# def get_tabled_headers(selected_table):
#     return [coll.name for coll in get_db().get_table(get_tables()[selected_table]).columns]


@app.route("/<int:selected_table>/")
@app.route("/")
def index(selected_table=-1):
    models.kek_print('start index')
    data = {}
    tables = get_tables()

    data['tables_titles'] = [table.title for table in tables]

    if 0 <= selected_table < len(tables):
        data['selected_table'] = selected_table

        selected_model = tables[selected_table]()

        data['fields_titles'] = selected_model.fields_titles

        search_field = misc.get_positive_int(request.args.get('search_field', -1))
        search_val = request.args.get('search_val', None)

        if search_field >= 0 and search_val:
            data['entries'] = selected_model.fetch_all_by_criteria(search_field, search_val)
        else:
            data['entries'] = selected_model.fetch_all()

    return render_template('list.html', **data)

