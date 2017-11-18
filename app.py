from flask import Flask
from flask import request
from flask import render_template
import models
import misc

app = Flask(__name__)

#TODO: investigate crashes
#@app.teardown_appcontext
# def on_teardown(error):
#     models.close_db(error)


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


@app.route("/<int:selected_table>/")
@app.route("/")
def index(selected_table=-1):
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
            data['search_val'] = search_val
            data['search_field'] = search_field
            data['entries'] = selected_model.fetch_all_by_criteria(search_field, search_val)
        else:
            data['entries'] = selected_model.fetch_all()

    return render_template('list.html', **data)

