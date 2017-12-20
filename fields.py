import fields_html
from collections import OrderedDict

class BaseField:
    def __init__(self, title, col_name, table_name=None):
        self.title = title
        self.col_name = col_name
        self.table_name = table_name
        self.target_model = None

    def select_col_raw(self, sql_builder):
        sql_builder.add_field(self.col_name)

    @property
    def qualified_col_name(self):
        return '{}.{}'.format(self.table_name, self.col_name)

    @property
    def resolved_name(self):
        return self.qualified_col_name

    def get_html(self, value=None, **kwargs):
        return fields_html.string_field(self, value, **kwargs)

    def get_all_values(self):
        model = self.target_model
        values = model.fetch_all([self, self], pack=False)
        return OrderedDict((val[0], val[1]) for val in values)


class IntegerField(BaseField):
    def get_html(self, value=None, **kwargs):
        return fields_html.int_field(self, value, **kwargs)


class PKField(IntegerField):
    def __init__(self, title='ID', col_name='ID'):
        super().__init__(title, col_name)

    def get_html(self, value=None, **kwargs):
        return fields_html.int_field(self, value, **kwargs)


class ForeignKeyField(BaseField):
    def __init__(self, title, col_name, target_model_class, target_fields=(), target_pk='id'):
        super().__init__(title, col_name)
        self.target_pk = target_pk
        self.target_fields = target_fields
        self.target_model = target_model_class()

        for f_name, f_title in self.target_fields:
            self.target_model.get_field_by_col_name(f_name).title = f_title

    def __getattr__(self, item):
        return getattr(self.target_model, item)

    def get_html(self, value=None, **kwargs):
        model = self.target_model
        choices = model.fetch_all([model.pk, model.main_field], pack=False)
        return fields_html.fk_field(self, value, choices=choices, pk_col_name=model.pk.qualified_col_name, **kwargs)

    @property
    def resolved_name(self):
        return self.target_model.main_field.qualified_col_name

    def get_all_values(self):
        model = self.target_model
        values = model.fetch_all([model.pk, model.main_field], pack=False)
        return OrderedDict((val[0], val[1]) for val in values)


class StringField(BaseField):
    def __init__(self, title=None, col_name=None):
        super().__init__(title, col_name)


class TimestampField(BaseField):
    def __init__(self, title=None, col_name=None):
        super().__init__(title, col_name)
