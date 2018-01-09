from flask import Flask
from flask import request
from flask import redirect
from flask import url_for
from flask import jsonify
from flask import abort
import models
import misc
import type_checkers
import jinja_helpers
from conditions import BasicCondition, create_conditions
from datetime import datetime
from collections import OrderedDict
import conflicts

app = Flask(__name__)
jinja_helpers.register_helpers(app)

#TODO: investigate crashes
@app.teardown_appcontext
def on_teardown(error):
    models.close_db(error)


tables = OrderedDict({model.title.lower(): model for model in models.all_models})
pagination_choices = (10, 20, 50)

'''------------'''
'''MISC HELPERS'''
'''------------'''


def get_page_size():
    choice = request.args.get('page_size', pagination_choices[0], type=type_checkers.ge_int(1))
    if choice not in pagination_choices:
        choice = pagination_choices[0]
    return choice


def get_search_fields(selected_model, data):
    data['logic_search_operators_list'] = BasicCondition.logic_operators
    data['compare_search_operators_list'] = BasicCondition.compare_operators

    data['query_params']['logic_operator'] = request.args.getlist('logic_operator', type=type_checkers.logic_operators)
    data['query_params']['compare_operator'] = request.args.getlist('compare_operator', type=type_checkers.compare_operators)

    data['query_params']['search_field'] = request.args.getlist('search_field', type=type_checkers.model_field(selected_model))
    data['query_params']['search_val'] = request.args.getlist('search_val')

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
    page = request.args.get('page', 1, type=type_checkers.ge_int(1))
    query_params['page'] = page
    query_params['page_size'] = page_size

    if table not in tables:
        return data

    selected_model = tables[table]()
    get_search_fields(selected_model, data)
    # PAGINATION
    pagination = (page, page_size)

    data['selected_table'] = table

    data['fields'] = selected_model.fields_short_resolved
    data['pk'] = selected_model.pk

    # SORTING
    sort_field = request.args.get('sort_field', None, type=type_checkers.model_field(selected_model))
    sort_order = request.args.get('sort_order', None, type=type_checkers.sort_order)

    query_params['sort_field'] = sort_field
    query_params['sort_order'] = sort_order
    data['last_update'] = datetime.now().timestamp()

    if data['query_params']['search_field'] and data['query_params']['search_val']:
        conditions = create_conditions(data['query_params']['search_field'], data['query_params']['search_val'],
                                       data['query_params']['compare_operator'], data['query_params']['logic_operator'])

        data['entries'] = selected_model.fetch_all(conditions=conditions, sort_field=sort_field, sort_order=sort_order, pagination=pagination)
        data['pages'] = selected_model.get_pages(data['query_params']['search_field'], conditions, pagination)
    else:
        data['entries'] = selected_model.fetch_all(sort_field=sort_field, sort_order=sort_order, pagination=pagination)
        data['pages'] = selected_model.get_pages(pagination=pagination)

    return data


@app.route("/<table>/edit/<int:pk>", methods=['GET', 'POST'])
@misc.templated('edit.html')
def edit(table, pk):
    data = {}

    if table not in tables:
        return data

    model = tables[table]()
    data['table'] = table
    data['pk'] = pk
    fields = model.fields_no_pk
    data['fields'] = fields

    values = None
    deleted = False

    if request.method == 'POST':
        action = request.form.get('action', None)
        last_updated = request.form.get('last_update', type=float)

        if not last_updated:
            abort(404)

        # TODO: refactor
        log = models.LogModel()
        status = log.get_status(pk, model.table_name, datetime.fromtimestamp(last_updated), datetime.now())

        if status == 'MODIFIED':
            old_values = {field.qualified_col_name: request.form.get(field.qualified_col_name, None) for field in fields}
            modified_values = model.fetch_by_pk(pk, model.fields_short_resolved)
            data['already_modified'] = True
            data['modified_values'] = modified_values
            data['values'] = old_values
            data['last_update'] = datetime.now().timestamp()
            return data

        if action == 'delete':
            values = model.delete_by_pk(pk_val=pk, return_fields=model.fields)
            deleted = values is not None
            data['record_name'] = values[model.main_field.qualified_col_name]
        elif action == 'close' or action == 'edit':
            new_fields = {field.qualified_col_name: request.form.get(field.qualified_col_name, None) for field in fields}
            # test updating deleted record
            values = model.update(return_fields=model.fields, new_fields=new_fields, pk_val=pk)
            data['close_window'] = action == 'close'
    else:
        values = model.fetch_by_pk(pk, model.fields)

    if not values or all(v is None for v in values.values()):
        abort(404)

    data['last_update'] = datetime.now().timestamp()
    data['deleted'] = deleted
    data['values'] = values
    return data


@app.route("/<table>/create", methods=['GET', 'POST'])
@misc.templated('create.html')
def create(table):
    data = {}

    if table not in tables:
        return data

    model = tables[table]()

    fields = model.fields_no_pk
    data['fields'] = fields

    values = {}
    for field in fields:
        val = request.args.get(field.qualified_col_name, None)
        if val is not None:
            values[field.qualified_col_name] = val

    data['values'] = values

    if request.method == 'POST':
        new_fields = {field.qualified_col_name: request.form.get(field.qualified_col_name, None) for field in fields}
        pk = model.insert(new_fields)

        action = request.form.get('action', None)

        if action == 'edit':
            return redirect(url_for('edit', table=table, pk=pk))
        elif action == 'close':
            data['close_window'] = True
        # elif action == 'new' or action is None:
        #     pass

    return data


@app.route('/analytics/<table>')
@app.route('/analytics/')
@misc.templated('analytics.html')
def analytics(table=None):
    data = {}
    query_params = {}
    data['query_params'] = query_params

    data['navigation_controller'] = 'analytics'
    data['tables'] = tables

    if table not in tables:
        return data

    model = tables[table]()
    get_search_fields(model, data)

    data['selected_table'] = table
    data['fields'] = model.fields_short_resolved
    data['analytics_fields'] = model.fields_no_pk

    data['pk_col_name'] = model.pk.qualified_col_name

    data['show_titles'] = request.args.get('show_titles', None);

    x_field_name = request.args.get('x_field', None, type=type_checkers.model_field_own(model))
    y_field_name = request.args.get('y_field', None, type=type_checkers.model_field_own(model))

    if not (x_field_name or y_field_name):
        return data

    x_field = model.get_field_by_col_name(x_field_name)
    y_field = model.get_field_by_col_name(y_field_name)

    data['x_field'] = x_field
    data['y_field'] = y_field

    data['x_field_name'] = x_field_name
    data['y_field_name'] = y_field_name

    show_fields = request.args.getlist('show_fields', type=type_checkers.model_field(model))

    if not show_fields:
        show_fields = {field.resolved_name for field in data['fields'] if field.resolved_name != x_field.resolved_name
                       and field.resolved_name != y_field.resolved_name and field.resolved_name != model.pk.resolved_name}

    data['show_fields'] = show_fields

    analytics_table = {}

    all_x = x_field.get_all_values()
    all_x.update({'None': 'None'})
    all_y = y_field.get_all_values()
    all_y.update({'None': 'None'})

    for y in all_y:
        analytics_table[y] = {x:[] for x in all_x}

    conditions = create_conditions(data['query_params']['search_field'], data['query_params']['search_val'],
                                   data['query_params']['compare_operator'], data['query_params']['logic_operator'])

    records = model.fetch_all(return_fields=model.fields_resolved, conditions=conditions)

    for record in records:
        x = record[x_field.qualified_col_name]
        x = x if x else 'None'
        y = record[y_field.qualified_col_name]
        y = y if y else 'None'
        analytics_table[y][x].append({field.qualified_col_name: record[field.resolved_name] for field in model.fields_short_resolved})

    data['analytics_table'] = analytics_table
    data['all_x'] = all_x
    data['all_y'] = all_y
    return data


@app.route('/update/<table>', methods=['POST'])
def update(table):
    if table not in tables:
        abort(404)

    model = tables[table]()
    fields = model.fields
    values = {}
    for field in fields:
        val = request.form.get(field.qualified_col_name.lower(), None)
        if val is not None:
            values[field.qualified_col_name] = val

    pk = request.form.get('pk', type=int)

    pk = model.update(return_fields=[model.pk], new_fields=values, pk_val=pk)
    return jsonify({'pk': pk})


@app.route("/<table>/log/", methods=['GET'])
def get_log(table):
    data = {}

    last_updated = request.args.get('last_update', None, type=float)

    if table not in tables or last_updated is None:
        data = 'error'
        return jsonify(data)

    model = tables[table]()

    pks = request.args.getlist('pk', type=int)

    logs = models.LogModel()

    statuses = dict(logs.get_statuses(pks, model.table_name, datetime.fromtimestamp(last_updated), datetime.now()))

    updating_pks = [pk for pk in pks if pk in statuses]

    # TODO: check for foreign tables
    # for pk in pks:
    #     if pk in updating_pks:
    #         continue
    #
    #     if :

    values = model.fetch_by_pks(updating_pks, model.fields_short_resolved)

    data['values'] = dict(zip(updating_pks, values))
    data['last_update'] = datetime.now().timestamp()
    data['statuses'] = statuses
    return jsonify(data)


@app.route('/<table>/log/<int:pk>.json', methods=['GET'])
def record_get(table, pk):
    data = {}

    last_updated = request.args.get('last_update', None, type=float)
    values = None

    if table not in tables or last_updated is None:
        abort(404)

    model = tables[table]()
    fields = model.fields_no_pk

    now_update = datetime.now()
    data['last_update'] = now_update.timestamp()

    last_updated = datetime.fromtimestamp(last_updated)

    log = models.LogModel()
    status = log.get_status(pk, model.table_name, last_updated, now_update)

    if status is None and model.fields_fks:
        fks_values = model.fetch_by_pk(pk, model.fields_fks)
        for fk in model.fields_fks:
            f_table_status = log.get_status(fks_values[fk.qualified_col_name], fk.pk.table_name, last_updated, now_update)
            if f_table_status == 'MODIFIED' or f_table_status == 'DELETED':
                status = 'MODIFIED'
                break

    if status == 'MODIFIED':
        values = model.fetch_by_pk(pk, model.fields_short_resolved_no_pk)

    data['status'] = status
    data['values'] = values

    return jsonify(data)

@app.route('/conflicts_list/<conflict_type>', methods=['GET', 'POST'])
@app.route('/conflicts_list', methods=['GET', 'POST'])
@misc.templated('conflicts.html')
def conflicts_list(conflict_type=None):
    data = {}

    conflicts_model = models.SchedConflicstModel()

    if request.method == 'POST':
        action = request.form.get('action', None)

        if action == 'recalc':
            data['recalc'] = True
            conflicts_model.full_recalc()

    if not conflict_type:
        return data

    conflict_type = conflict_type.lower()

    conflict = None
    for con in conflicts.all_conflicts:
        if conflict_type == con.alias.lower():
            conflict = con

    if not conflict:
        return data


    return data

app.run(debug=True)
