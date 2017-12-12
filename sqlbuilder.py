from conditions import BasicCondition
from fields import ForeignKeyField, BaseField
from collections import OrderedDict


class SQLBasicBuilder:
    def __init__(self, operation, target_table, fields=None, return_fields=None):
        self.operation = operation
        self.target_model = target_table
        self.fields = fields
        self.pagination = ()
        self.conditions = []
        self.params_after_where = []
        self.params_before_where = []
        self.return_fields = return_fields

    @property
    def query(self):
        return self.operation + ' '

    def _append_condition(self, condition):
        # Exclude fields with empty values
        if not condition.value:
            return
        self.conditions.append(condition)

    def add_conditions(self, conditions):
        if conditions is None:
            return

        try:
            for condition in conditions:
                self._append_condition(condition)
        except TypeError:
            self._append_condition(conditions)

    def add_equal_condition(self, field_name, value, logic_operator='AND'):
        self.add_conditions(BasicCondition(field_name, value, '=', logic_operator))

    def execute(self, cur):
        params = self.params_before_where

        for cond in self.conditions:
            cond.add_values(params)

        params += self.params_after_where
        print(self.query)
        print(params)
        return cur.execute(self.query, params)

    @property
    def conditions_query(self):
        query = ''
        if self.conditions:
            query += "WHERE "

        first = True
        for cond in self.conditions:
            query += cond.get_query_str(not first)
            first = False

        return query

    @property
    def returning_fields_query(self):
        if self.return_fields:
            return 'RETURNING ' + ', '.join(field.qualified_col_name for field in self.return_fields)
        return ''


class SQLBasicInsert(SQLBasicBuilder):
    def __init__(self, target_table=None, fields=None, return_fields=None):
        fields = OrderedDict(fields)
        super().__init__('INSERT', target_table, fields, return_fields)

        self.params_before_where += [value if value != 'None' else None for value in fields.values()]

    @property
    def inserting_fields_query(self):
        fields_str = ', '.join(self.fields)
        values_str = ', '.join('?' for field in self.fields)
        return '({}) VALUES ({})'.format(fields_str, values_str)

    @property
    def query(self):
        compiled_query = super().query
        compiled_query += 'INTO ' + self.target_model.table_name + ' '
        compiled_query += self.inserting_fields_query
        compiled_query += self.returning_fields_query
        return compiled_query


class SQLBasicUpdate(SQLBasicBuilder):
    def __init__(self, target_table, new_fields, return_fields=None):
        self.new_fields = new_fields
        super().__init__(operation='UPDATE', target_table=target_table, fields=[field for field in self.new_fields], return_fields=return_fields)
        self.params_before_where += [value if value != 'None' else None for value in self.new_fields.values()]

    @property
    def query(self):
        compiled_query = super().query
        compiled_query += self.target_model.table_name + ' SET '
        compiled_query += self.updating_fields_query
        compiled_query += self.conditions_query
        compiled_query += self.returning_fields_query

        return compiled_query

    @property
    def updating_fields_query(self):
        return ', '.join(field + ' = ? ' for field in self.fields)


class SQLBasicDelete(SQLBasicBuilder):
    def __init__(self, target_table=None, return_fields=None):
        super().__init__('DELETE', target_table, return_fields=return_fields)
        self.return_fields=return_fields

    @property
    def query(self):
        compiled_query = super().query
        compiled_query += 'from ' + self.target_model.table_name + ' '
        compiled_query += self.conditions_query
        compiled_query += self.returning_fields_query

        return compiled_query


class SQLBasicSelect(SQLBasicBuilder):
    def __init__(self, target_table, fields, sort_field=None, sort_order=None, rows=None):
        super().__init__('SELECT', target_table, fields)
        self.sort_field_name = sort_field
        self.sort_order = sort_order
        self.rows = rows

    @property
    def left_joins(self):
        return (field for field in self.target_model.fields if isinstance(field, ForeignKeyField))

    @property
    def selected_fields_query(self):
        return ', '.join(field.qualified_col_name for field in self.fields) + ' '

    @property
    def rows_query(self):
        query = ''
        if self.rows is not None:
            query = 'ROWS ? '
        return query

    @property
    def left_joins_query(self):
        query = ''
        for field in self.left_joins:
            query += 'LEFT JOIN {target_table} on {from_table}.{col_name}={target_table}.{target_pk} '.format(
                target_table=field.target_model.table_name,
                col_name=field.col_name,
                target_pk=field.target_pk,
                from_table=self.target_model.table_name
            )
        return query

    @property
    def query(self):
        compiled_query = super().query
        compiled_query += self.selected_fields_query
        compiled_query += 'from ' + self.target_model.table_name + ' '
        compiled_query += self.left_joins_query

        compiled_query += self.conditions_query
        return compiled_query


class SQLLogSelect(SQLBasicSelect):
    def __init__(self, target_table, fields):
        super().__init__(target_table, fields)

    @property
    def query(self):
        compiled_query = self.operation + ' '
        compiled_query += self.selected_fields_query
        compiled_query += 'from ' + self.target_model.table_name + ' '
        compiled_query += self.left_joins_query
        compiled_query += 'inner join (select {table_pk}, {table_name}, max({change_time}) {change_time} ' \
                          'from {log} GROUP BY {table_pk}, {table_name}) l1 on l1.{table_pk} = {outer_table_pk} and ' \
                          'l1.{table_name} = {outer_table_name} and ' \
                          'l1.{change_time} = {outer_change_time} '.format(table_pk=self.target_model.logged_table_pk.col_name,
                                                                          table_name=self.target_model.logged_table_name.col_name,
                                                                          change_time=self.target_model.datetime.col_name,
                                                                          log=self.target_model.table_name,
                                                                          outer_table_pk=self.target_model.logged_table_pk.qualified_col_name,
                                                                          outer_table_name=self.target_model.logged_table_name.qualified_col_name,
                                                                          outer_change_time=self.target_model.datetime.qualified_col_name)

        compiled_query += self.conditions_query
        return compiled_query


class SQLCountAll(SQLBasicSelect):
    def __init__(self, target_table):
        super().__init__(target_table, fields=[target_table.pk])

    @property
    def selected_fields_query(self):
        return 'COUNT(*) '


class SQLSelect(SQLBasicSelect):
    def __init__(self, target_table, fields, pagination=None, rows=None):
        super().__init__(target_table, fields, rows=rows)
        self.pagination = pagination

        if self.pagination:
            page = self.pagination[0]
            page_size = self.pagination[1]
            self.params_after_where.append(page_size * (page - 1))
            self.params_after_where.append(page_size)

        if self.rows:
            self.params_after_where.append(rows)

    @property
    def offset_query(self):
        query = ''
        if self.pagination:
            query = 'OFFSET ? ROWS FETCH FIRST ? ROWS ONLY '
            page = self.pagination[0]
            page_size = self.pagination[1]

        return query

    @property
    def sort_query(self):
        query = ''
        if self.sort_field_name is not None:
            query += 'ORDER BY ' + self.sort_field_name + ' '

            if self.sort_order:
                query += self.sort_order + ' '
        return query

    @property
    def query(self):
        compiled_query = super().query
        compiled_query += self.sort_query
        compiled_query += self.offset_query
        compiled_query += self.rows_query
        return compiled_query


