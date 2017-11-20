from flask import request
from werkzeug.urls import url_encode


def modify_query(**new_values):
    args = request.args.copy()

    for key, value in new_values.items():
        args[key] = value

    return '{}?{}'.format(request.path, url_encode(args))


def register_helpers(app):
    app.add_template_global(modify_query)
    app.add_template_filter(max_val)
    app.add_template_filter(min_val)


def max_val(l):
    return max(l)


def min_val(l):
    return min(l)