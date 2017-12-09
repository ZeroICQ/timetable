class BaseField:
    def __init__(self, title, col_name, table_name=None):
        self.title = title
        self.col_name = col_name
        self.table_name = table_name

    def select_col_raw(self, sql_builder):
        sql_builder.add_field(self.col_name)

    @property
    def qualified_col_name(self):
        return '{}.{}'.format(self.table_name, self.col_name)


class IntegerField(BaseField):
    pass


class PKField(IntegerField):
    def __init__(self, title='ID', col_name='ID'):
        super().__init__(title, col_name)


class ForeignKeyField(BaseField):
    def __init__(self, title, col_name, target_model, target_fields=(), target_pk='id'):
        super().__init__(title, col_name)

        self.target_pk = target_pk
        self.target_fields = target_fields
        self.target_model = target_model


class StringField(BaseField):
    def __init__(self, title=None, col_name=None):
        super().__init__(title, col_name)


class TimestampField(BaseField):
    def __init__(self, title=None, col_name=None):
        super().__init__(title, col_name)