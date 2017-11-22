from flask import Flask
from flask import request
from flask import render_template
import models
import misc
import jinja_helpers
from conditions import BaseCondition

app = Flask(__name__)
jinja_helpers.register_helpers(app)

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


def get_pagination_choices():
    choices = (
        5, 10, 20
    )
    return choices


@app.route("/<int:selected_table>/")
@app.route("/")
def index(selected_table=-1):
    data = {}
    tables = get_tables()

    data['tables_titles'] = [table.title for table in tables]
    pagination_choices = get_pagination_choices()
    data['pagination_choices'] = pagination_choices

    if 0 <= selected_table < len(tables):
        data['selected_table'] = selected_table

        selected_model = tables[selected_table]()

        data['fields_titles'] = selected_model.fields_titles

        search_fields = request.args.getlist('search_field', type=misc.mt_int(0))
        search_vals = request.args.getlist('search_val')

        logic_operators = request.args.getlist('logic_operator', type=misc.mt_int(0))
        compare_operators = request.args.getlist('compare_operator', type=misc.mt_int(0))

        data['logic_search_operators_list'] = BaseCondition.logic_operators
        data['compare_search_operators_list'] = BaseCondition.compare_operators

        pagination_choice = request.args.get('pagination_choice', 0, type=misc.mt_int(0))
        page = request.args.get('page', 1, type=misc.mt_int(1))
        sort_field = request.args.get('sort', None, type=misc.mt_int(0))
        data['sort_field'] = sort_field

        selected_model.pagination = (pagination_choices[pagination_choice] * (page-1), pagination_choices[pagination_choice])
        data['page'] = page
        data['pagination_choice'] = pagination_choice

        if search_fields and search_vals:
            data['search_vals'] = search_vals
            data['search_fields'] = search_fields
            data['entries'] = selected_model.fetch_all_by_criteria(search_fields, search_vals, logic_operators,
                                                                   compare_operators, sort_field)
            data['pages'] = selected_model.get_pages(search_fields, search_vals, logic_operators, compare_operators)
            data['logic_operators'] = logic_operators
            data['compare_operators'] = compare_operators
            data['search_vals'] = search_vals
        else:
            data['entries'] = selected_model.fetch_all()
            data['pages'] = selected_model.get_pages()

    return render_template('list.html', **data)

#app.run(debug=True)
