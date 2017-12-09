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
from collections import OrderedDict

app = Flask(__name__)
jinja_helpers.register_helpers(app)

#TODO: investigate crashes
# @app.teardown_appcontext
# def on_teardown(error):
#     models.close_db(error)


tables = OrderedDict({model.title.lower(): model for model in models.all_models})
pagination_choices = (10, 20, 50)

'''------------'''
'''MISC HELPERS'''
'''------------'''


def get_page_size():
    choice = request.args.get('page_size', pagination_choices[0], type=misc.ge_int(1))
    if choice not in pagination_choices:
        choice = pagination_choices[0]
    return choice


'''-----------'''
'''CONTROLLERS'''
'''-----------'''


@app.route("/<table>/")
@app.route("/")
@misc.templated('catalog.html')
def catalog(table=''):
    data = {}
    query_params = {}
    data['query_params'] = query_params

    data['tables'] = tables
    data['pagination_choices'] = pagination_choices

    table = table.lower()

    # PARSE PARAMETERS
    page_size = get_page_size()
    page = request.args.get('page', 1, type=misc.ge_int(1))
    query_params['page'] = page
    query_params['page_size'] = page_size

    if table not in tables:
        return data

    selected_model = tables[table]()

    # PAGINATION
    # selected_model.pagination = (page_size * (page - 1), page_size)
    pagination = (page, page_size)

    data['selected_table'] = table

    data['fields'] = selected_model.fields_no_fk
    # data['last_update'] = datetime.now().timestamp()

    # search_fields = request.args.getlist('search_field', type=misc.ge_int(0))
    # search_vals = request.args.getlist('search_val')

    # logic_operators = request.args.getlist('logic_operator', type=misc.ge_int(0))
    # compare_operators = request.args.getlist('compare_operator', type=misc.ge_int(0))

    # data['logic_search_operators_list'] = BasicCondition.logic_operators
    # data['compare_search_operators_list'] = BasicCondition.compare_operators

    # sort_field = request.args.get('sort_field', None, type=misc.ge_int(0))
    # sort_order = request.args.get('sort_order', None, type=misc.sort_order)
    #
    # query_params['sort_field'] = sort_field
    # query_params['sort_order'] = sort_order
    #


    #
    # if search_fields and search_vals:
    #     query_params['search_field'] = search_fields
    #     query_params['search_val'] = search_vals
    #     data['entries'] = selected_model.fetch_all_by_criteria(search_fields, search_vals, logic_operators,
    #                                                            compare_operators, sort_field, sort_order)
    #     data['pages'] = selected_model.get_pages(search_fields, search_vals, logic_operators, compare_operators)
    #     query_params['logic_operator'] = logic_operators
    #     query_params['compare_operator'] = compare_operators
    #     query_params['search_val'] = search_vals
    # else:
    data['entries'] = selected_model.fetch_all(pagination=pagination)
    data['pages'] = selected_model.get_pages(pagination=pagination)

    return data


@app.route("/<table>/edit/<int:pk>", methods=['GET', 'POST'])
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
        action = request.form.get('action', None)
        if action == 'close':
            data['close_window'] = True
            return data

    data['values'] = model.fetch_raw_by_pk(pk)

    return data


@app.route("/<table>/delete/<int:pk>", methods=['GET', 'POST'])
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


@app.route("/<table>/create", methods=['GET', 'POST'])
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


@app.route("/<table>/log/", methods=['GET'])
def get_log(table):
    data = {}
    tables = get_tables()

    last_update = request.args.get('last_update', None, type=float)

    if not (0 <= table < len(tables)) or last_update is None:
        return jsonify(data)

    last_update = datetime.fromtimestamp(last_update)

    pks = request.args.getlist('pk', type=int)
    logs = models.LogModel()
    changes = logs.get_changes(last_update, pks, tables[table]().table_name)

    ch_dict = {}
    for change in changes:
        ch_dict[change.get(logs.logged_table_pk.col_name)] = change.get(logs.status.target_fields[0][0])

    data['changes'] = ch_dict
    data['last_update'] = datetime.now().timestamp()

    return jsonify(data)


@app.route('/<table>/get', methods=['GET'])
def record_get(table, pk=None):
    data = {}
    tables = get_tables()

    pk = request.args.get('pk', None, type=int);

    if not (0 <= table < len(tables)):
        return jsonify(data)

    model = tables[table]()

    data = model.fetch_by_pk(pk_val=pk)
    return jsonify(data)


app.run(debug=True)
