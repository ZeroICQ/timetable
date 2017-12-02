class BaseField:
    def __init__(self, title=None, col_name=None):
        self._title = title
        self.col_name = col_name

    def select_col(self, sql_builder):
        sql_builder.add_field(self.col_name)

    def select_col_raw(self, sql_builder):
        sql_builder.add_field(self.col_name)

    @property
    def title(self):
        return self._title


class IntegerField(BaseField):
    def __init__(self, title=None, col_name=None):
        super().__init__(title, col_name)


class PKField(IntegerField):
    def __init__(self, title='ID', col_name='ID'):
        super().__init__(title, col_name)


class ForeignKeyField(BaseField):
    def __init__(self, title=None, col_name=None, target_table=None,
                 target_fields=(), target_pk='id', target_title=None):
        super().__init__(title, col_name)

        self.target_pk = target_pk
        self.target_fields = target_fields
        self.target_table = target_table
        self.target_title = target_title

    def select_col(self, sql_builder):
        for field in self.target_fields:
            sql_builder.add_field(field[0], self.target_table)

        sql_builder.add_left_join(self)

    @property
    def title(self):
        return [target_field[1] for target_field in self.target_fields]


class StringField(BaseField):
    def __init__(self, title=None, col_name=None):
        super().__init__(title, col_name)
