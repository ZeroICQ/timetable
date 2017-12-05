from flask import Flask
from flask import request
from flask import render_template
from flask import redirect
from flask import url_for
from flask import jsonify
import models
import misc
import jinja_helpers
from conditions import BasicCondition
from datetime import  datetime


app = Flask(__name__)
jinja_helpers.register_helpers(app)

#TODO: investigate crashes
# @app.teardown_appcontext
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
        models.WeekdaysModel,
        models.LogStatusModel,
        models.LogModel
    )
    return tables


def get_pagination_choices():
    choices = (
        5, 10, 20
    )
    return choices


@app.route("/<int:selected_table>/")
@app.route("/")
@misc.templated('list.html')
def index(selected_table=-1):
    data = {}
    query_params = {}
    data['query_params'] = query_params

    tables = get_tables()

    data['tables_titles'] = [table.title for table in tables]
    pagination_choices = get_pagination_choices()
    data['pagination_choices'] = pagination_choices

    if not (0 <= selected_table < len(tables)):
        return data

    data['selected_table'] = selected_table

    selected_model = tables[selected_table]()

    data['fields_titles'] = selected_model.fields_titles

    search_fields = request.args.getlist('search_field', type=misc.ge_int(0))
    search_vals = request.args.getlist('search_val')

    logic_operators = request.args.getlist('logic_operator', type=misc.ge_int(0))
    compare_operators = request.args.getlist('compare_operator', type=misc.ge_int(0))

    data['logic_search_operators_list'] = BasicCondition.logic_operators
    data['compare_search_operators_list'] = BasicCondition.compare_operators

    pagination_choice = request.args.get('pagination_choice', 0, type=misc.ge_int(0))
    page = request.args.get('page', 1, type=misc.ge_int(1))
    sort_field = request.args.get('sort_field', None, type=misc.ge_int(0))
    sort_order = request.args.get('sort_order', None, type=misc.sort_order)

    query_params['sort_field'] = sort_field
    query_params['sort_order'] = sort_order

    selected_model.pagination = (pagination_choices[pagination_choice] * (page-1), pagination_choices[pagination_choice])
    query_params['page'] = page
    query_params['pagination_choice'] = pagination_choice

    if search_fields and search_vals:
        query_params['search_field'] = search_fields
        query_params['search_val'] = search_vals
        data['entries'] = selected_model.fetch_all_by_criteria(search_fields, search_vals, logic_operators,
                                                               compare_operators, sort_field, sort_order)
        data['pages'] = selected_model.get_pages(search_fields, search_vals, logic_operators, compare_operators)
        query_params['logic_operator'] = logic_operators
        query_params['compare_operator'] = compare_operators
        query_params['search_val'] = search_vals
    else:
        data['entries'] = selected_model.fetch_all(sort_field, sort_order)
        data['pages'] = selected_model.get_pages()

    return data


@app.route("/<int:table>/edit/<int:pk>", methods=['GET', 'POST'])
@misc.templated('edit.html')
def edit(table=None, pk=None):
    data = {}
    tables = tables = get_tables()

    if not (0 <= table < len(tables)):
        return data

    model = tables[table]()
    fields = model.mutable_fields
    data['fields'] = fields

    if request.method == 'POST':
        values = [request.form.get(str(i), None) for i in range(len(fields))]
        model.update(fields, values, pk)

    data['values'] = model.fetch_raw_by_pk(pk)

    return data


@app.route("/<int:table>/delete/<int:pk>", methods=['GET', 'POST'])
@misc.templated('delete.html')
def delete(table=None, pk=None):
    data = {}
    tables = tables = get_tables()

    if not (0 <= table < len(tables)):
        return data

    model = tables[table]()
    fields = model.mutable_fields
    data['fields'] = fields
    data['values'] = model.fetch_raw_by_pk(pk)

    if request.method == 'POST':
        model.delete_by_id(pk_val=pk)
        data['status'] = 'ok'
        data['close_window'] = True

    return data


@app.route("/<int:table>/create", methods=['GET', 'POST'])
@misc.templated('create.html')
def create(table=None):
    data = {}
    tables = get_tables()

    if not (0 <= table < len(tables)):
        return data

    model = tables[table]()
    fields = model.mutable_fields
    data['fields'] = fields

    if request.method == 'POST':
        values = [request.form.get(str(i), None) for i in range(len(fields))]
        pk = model.insert(values)
        action = request.form.get('action', None)

        if action == 'edit':
            redirect(url_for('edit',table=table, pk=pk))
        elif action == 'close':
            data['close_window'] = True
        # elif action == 'new' or action is None:
        #     pass

    return data


@app.route("/<int:table>/log/", methods=['GET'])
def get_log(table):
    data = {}
    tables = get_tables()

    if not (0 <= table < len(tables)):
        return jsonify(data)
    last_update = request.args.get('last_updated', type=int)
    last_update = datetime.fromtimestamp(last_update/1000) #convert from js

    ll = models.LogModel()
    ll.get_changes(last_update, [1,2], 'AUDIENCES')
    data['last_update'] = last_update

    return jsonify(data)
# select * from LOG l
# where l.CHANGE_TIME>'2017-12-06' and l.CHANGE_TIME = (select max(l1.CHANGE_TIME) from LOG l1 where l1.table_pk = l.table_pk)
# order by l.TABLE_PK


app.run(debug=True)
