def mt_int(lbound:int):
    def f(val):
        val = int(val)
        if val < lbound:
            raise ValueError

        return val
    return f