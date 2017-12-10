class BasicWrapper:
    def __init__(self, field):
        super().__init__()
        self.field = field

    def __getattr__(self, name):
        return self.fied.name


class MaxWrapper(BasicWrapper):
    def __init__(self, field):
        super().__init__(field)

    @property
    def qualified_col_name(self):
        return 'max({})'.format(self.field.qualified_col_name)
