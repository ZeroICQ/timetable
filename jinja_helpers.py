from flask import request
from werkzeug.urls import url_encode
import flask
import copy


def register_helpers(app):
    app.add_template_global(modify_query)
    app.add_template_filter(max_val)
    app.add_template_filter(min_val)


def modify_query(query_params, **new_values):
    args = copy.deepcopy(query_params)

    for key, value in new_values.items():
        args[key] = value

    return '{}?{}'.format(request.path, url_encode(args))




def max_val(l):
    return max(l)


def min_val(l):
    return min(l)
