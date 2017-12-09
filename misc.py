from functools import wraps
from flask import request, render_template
import conditions

def ge_int(lbound):
    def f(val):
        val = int(val)
        if val < lbound:
            raise ValueError

        return val
    return f


def sort_order(val):
    val = str(val)
    val = val.upper()
    if val not in ['ASC', 'DESC']:
        raise ValueError

    return val


def model_field(model):
    def check_function(field_name):
        if field_name not in [field.qualified_col_name for field in model.fields_no_fk]:
            raise ValueError
        return field_name
    return check_function


def logic_operators(val):
    if val not in conditions.BasicCondition.logic_operators:
        raise ValueError
    return val


def compare_operators(val):
    if val not in conditions.BasicCondition.compare_operators:
        raise ValueError
    return val

def templated(template=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = request.endpoint \
                    .replace('.', '/') + '.html'
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return render_template(template_name, **ctx)
        return decorated_function
    return decorator
