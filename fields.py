class BaseField:
    def __init__(self, title=None, col_name=None, width=10):
        self._title = title
        self.col_name = col_name
        self.width = width

    def select_col(self, sql_builder):
        sql_builder.add_field(self.col_name)

    @property
    def title(self):
        return self._title


class IntegerField(BaseField):
    def __init__(self, title=None, col_name=None, width=10):
        super().__init__(title, col_name, width)


class PKField(IntegerField):
    def __init__(self, title='ID', col_name='ID', width=10):
        super().__init__(title, col_name, width)


class ForeignKeyField(BaseField):
    def __init__(self, title=None, col_name=None, width=10, target_table=None,
                 target_fields=(), target_pk='id'):
        super().__init__(title, col_name,  width)

        self.target_pk = target_pk
        self.target_fields = target_fields
        self.target_table = target_table

    def select_col(self, sql_builder):
        for field in self.target_fields:
            sql_builder.add_field(field[0], self.target_table)

        sql_builder.add_left_join(self)

    @property
    def title(self):
        return [target_field[1] for target_field in self.target_fields]


class StringField(BaseField):
    def __init__(self, title=None, col_name=None, width=50):
        super().__init__(title, col_name, width)
