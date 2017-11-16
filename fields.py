from sqlbuilder import SQLSelect


class BaseField:
    def __init__(self, title=None, width=10, col_name=None):
        self.title = title
        self.width = width
        self.col_name = col_name

    def get_title(self):
        return self.title

    def select_col(self, SQLBuilder: SQLSelect):
        SQLBuilder.add_col(self.col_name)


class IntegerField(BaseField):
    def __init__(self, title=None, width=10, col_name=None):
        super().__init__(title, width, col_name)


class PKField(IntegerField):
    def __init__(self, title='ID', width=10, col_name='ID'):
        super().__init__(title, width, col_name)


class ForeignKeyField(BaseField):
    def __init__(self, title=None, width=10, col_name=None, target_table=None,
                 target_fields=[], target_fields_titles=[], target_pk='id'):
        super().__init__(title, width, col_name)
        self.target_pk = target_pk
        self.target_fields = target_fields
        self.target_table_titles = target_fields_titles
        self.target_table = target_table

    def select_col(self, SQLBuilder: SQLSelect):
        for trgt in self.target_fields:
            SQLBuilder.add_col(trgt, self.target_table)

        SQLBuilder.add_left_join(self.target_table, self.col_name, self.target_pk)

    def get_title(self):
        return self.target_table_titles


class StringField(BaseField):
    def __init__(self, title=None, width=50, col_name=None):
        super().__init__(title, width, col_name)
