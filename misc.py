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
