import conditions
import conflicts

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
        if field_name.lower() not in [field.qualified_col_name.lower() for field in model.fields_short_resolved]:
            raise ValueError
        return field_name
    return check_function


def model_field_own(model):
    def check_function(field_name):
        if field_name.lower() not in [field.qualified_col_name.lower() for field in model.fields]:
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


def conflict(val):
    val = val.lower()
    for conflict in conflicts.all_conflicts:
        if val == conflict.alias.lower():
            return conflict
    raise ValueError