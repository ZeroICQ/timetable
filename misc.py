def mt_int(lbound):
    def f(val):
        val = int(val)
        if val < lbound:
            raise ValueError

        return val
    return f