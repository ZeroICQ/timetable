from flask import request
from werkzeug.urls import url_encode
import flask
import fields
import copy


def register_helpers(app):
    app.add_template_global(modify_query)
    app.add_template_global(form_field)
    app.add_template_filter(max_val)
    app.add_template_filter(min_val)


def modify_query(query_params, **new_values):
    args = copy.deepcopy(query_params)

    for key, value in new_values.items():
        args[key] = value

    return '{}?{}'.format(request.path, url_encode(args))


def markup(f):
    def wrap(field, val=None, *args, **kwargs):
        params = {
            'val': val if val else '',
            'label': field.title,
            'name': kwargs.get('name', '')
        }

        html = f(field, val, params)
        html = '<label>%(label)s</label>' + html
        return flask.Markup(html) % params
    return wrap


@markup
def _string_field(field, val, params=None):
    return '<input name="%(name)s" class="form-control form-control-sm" type="text" value="%(val)s">'


@markup
def _int_field(field, val, params=None):
    return '<input name="%(name)s" class="form-control form-control-sm" type="number" value="%(val)s">'


@markup
def _fk_field(field, val, params=None):
    params['label'] = field.target_title if field.target_title else field.target_table
    return '<input name="%(name)s" class="form-control form-control-sm" type="number" value="%(val)s">'


@markup
def _timestamp_field(field, val, params=None):
    return '<input name="%(name)s" class="form-control form-control-sm" type="datetime" value="%(val)s">'


def form_field(field, val='', **kwargs):
    if isinstance(field, fields.StringField):
        return _string_field(field, val, **kwargs)
    elif isinstance(field, fields.IntegerField):
        return _int_field(field, val, **kwargs)
    elif isinstance(field, fields.ForeignKeyField):
        return _fk_field(field, val, **kwargs)
    elif isinstance(field, fields.TimestampField):
        return _timestamp_field(field, val, **kwargs)
    else:
        return field


def max_val(l):
    return max(l)


def min_val(l):
    return min(l)
