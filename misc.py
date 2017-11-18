def get_positive_int(val):
    try:
        val = int(val)
    except ValueError:
        return -1

    return val