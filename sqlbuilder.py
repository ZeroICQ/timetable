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

    def add_condition(self, field_name, value, compare_operator, logic_operator='AND'):
        # Exclude fields with empty values
        if not value:
            return
        self.conditions.append(BasicCondition(field_name, value, logic_operator, compare_operator))

    def add_equal_condition(self, field_name, value, logic_operator=None):
        self.add_condition(field_name, value, '=', logic_operator)

    def execute(self, cur):
        params = self.params_before_where
        params += [cond.val for cond in self.conditions]
        params += self.params_after_where
        print(self.query)
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


class SQLLog(SQLBasicInsert):
    log_fields = ['status',
                  'table_name',
                  'table_pk']

    def __init__(self, target_table=None, values=None):
        super().__init__(target_table=target_table, values=values)

        for field in self.log_fields:
            self.add_field(field)


class SQLBasicUpdate(SQLBasicBuilder):
    def __init__(self, target_table, new_fields, return_fields=None):
        new_fields = OrderedDict(new_fields)
        super().__init__(operation='UPDATE', target_table=target_table, fields=[field for field in new_fields], return_fields=return_fields)
        self.new_fields = new_fields
        self.params_before_where += [value if value != 'None' else None for value in new_fields.values()]

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
    def __init__(self, target_table, fields, sort_field=None, sort_order=None):
        super().__init__('SELECT', target_table, fields)
        self.sort_field = sort_field
        self.sort_order = sort_order

    @property
    def left_joins(self):
        return (field for field in self.target_model.fields if isinstance(field, ForeignKeyField))

    @property
    def selected_fields_query(self):
        # return ', '.join(map(lambda f: f.qualified_col_name, self.fields)) + ' '
        return ', '.join(field.qualified_col_name for field in self.fields) + ' '

    @property
    def query(self):
        compiled_query = super().query
        compiled_query += self.selected_fields_query
        compiled_query += 'from ' + self.target_model.table_name + ' '

        for field in self.left_joins:
            compiled_query += 'LEFT JOIN {target_table} on {from_table}.{col_name}={target_table}.{target_pk} '.format(
                target_table=field.target_model.table_name,
                col_name=field.col_name,
                target_pk=field.target_pk,
                from_table=self.target_model.table_name
            )

        compiled_query += self.conditions_query
        return compiled_query


class SQLLogSelect(SQLBasicSelect):
    def conditions_query(self, query):
        query = super().conditions_query(query)
        subselect = 'AND {table_name}.{time_col_name} = (select max({tmp_table_name}.{time_col_name}) from {table_name} {tmp_table_name} ' \
                    'where {tmp_table_name}.{table_pk} = {table_name}.{table_pk}) '.format(
                        tmp_table_name=self.target_model.table_name + '1',
                        time_col_name=self.target_model.datetime.col_name,
                        table_name=self.target_model.table_name,
                        table_pk=self.target_model.logged_table_pk.col_name)

        query += subselect
        return query


class SQLCountAll(SQLBasicSelect):
    def __init__(self, target_table):
        super().__init__(target_table, fields=[target_table.pk])

    @property
    def selected_fields_query(self):
        return 'COUNT(*) '


class SQLSelect(SQLBasicSelect):
    def __init__(self, target_table, fields, pagination=None):
        super().__init__(target_table, fields)
        self.pagination = pagination

        if self.pagination:
            page = self.pagination[0]
            page_size = self.pagination[1]
            self.params_after_where.append(page_size * (page - 1))
            self.params_after_where.append(page_size)

    @property
    def offset_query(self):
        query = ''
        if self.pagination:
            query = 'OFFSET ? ROWS FETCH FIRST ? ROWS ONLY '
            page = self.pagination[0]
            page_size = self.pagination[1]

            self.params_after_where.append(page_size * (page - 1))
            self.params_after_where.append(page_size)
        return query

    @property
    def sort_query(self):
        query = ''
        if self.sort_field is not None:
            query += 'ORDER BY ' + self.sort_field + ' '

            if self.sort_order:
                query += self.sort_order + ' '
        return query

    @property
    def query(self):
        compiled_query = super().query
        compiled_query += self.sort_query
        compiled_query += self.offset_query
        return compiled_query
