from conditions import BasicCondition
from fields import ForeignKeyField, BaseField


class SQLBasicBuilder:
    def __init__(self, operation, target_table, fields):
        self.operation = operation
        self.target_model = target_table
        self.fields = fields
        self.pagination = ()
        self.conditions = []
        self.params = []

    @property
    def query(self):
        return self.operation + ' '

    def add_condition(self, field_name, value, logic_operator, compare_operator):
        # Exclude fields with empty values
        if not value:
            return
        self.conditions.append(BasicCondition(field_name, value, logic_operator, compare_operator))

    def add_where_equal_param(self, col_name, val, logic_operator=None):
        self.custom_conditions.append(CustomCondition(col_name, val, '=', logic_operator=logic_operator))

    @property
    def selected_fields_query(self):
        return ', '.join(map(lambda f: f.qualified_col_name, self.fields)) + ' '

    def execute(self, cur):
        params = [cond.val for cond in self.conditions]
        params += self.params
        print(self.query)
        return cur.execute(self.query, params)

    def get_conditions_query(self):
        query = ''
        if self.conditions:
            query += "WHERE "

        # first = True
        # TODO: delete
        # for cond in self.conditions:
        #     if first:
        #         first = False
        #     else:
        #         query += cond.logic_operator + ' '
        #
        #     query += '{0} {1} ? '.format(self.fields[cond.field], cond.compare_operator)
        first = True
        for cond in self.conditions:
            query += cond.get_query_str(not first)
            first = False

        return query


class SQLBasicInsert(SQLBasicBuilder):
    def __init__(self, target_table=None, values=None, operation='INSERT'):
        super().__init__(operation=operation, target_table=target_table)
        #very important check
        self.values = [value if value else None for value in values]

    def execute(self, cur, params=None):
        if params is None:
            params = []
        params += self.values
        return super().execute(cur, params)

    def add_field(self, field):
        self.fields.append(field)

    def add_inserting_fields(self, query):
        query += '('
        query += ', '.join(self.fields)
        query += ') VALUES ('
        query += ', '.join(['?' for field in self.fields])
        query += ') '

        return query

    @property
    def query(self):
        compiled_query = super().query
        compiled_query += 'INTO ' + self.target_model.table_name + ' '
        compiled_query = self.add_inserting_fields(compiled_query)
        compiled_query += ' RETURNING ' + self.target_model.pk.col_name
        return compiled_query


class SQLLog(SQLBasicInsert):
    log_fields = ['status',
                  'table_name',
                  'table_pk']

    def __init__(self, target_table=None, values=None):
        super().__init__(target_table=target_table, values=values)

        for field in self.log_fields:
            self.add_field(field)


class SQLBasicUpdate(SQLBasicInsert):
    def __init__(self, target_table, values=None):
        super().__init__(operation='UPDATE', target_table=target_table, values=values)

    @property
    def query(self):
        compiled_query = self.operation + ' ' + self.target_model.table_name + ' SET '
        compiled_query = self.add_updating_fields(compiled_query)
        compiled_query = self.get_conditions_query(compiled_query)
        compiled_query += ' RETURNING ' + self.target_model.pk.col_name

        return compiled_query

    def add_updating_fields(self, query):
        return query + ', '.join([field + ' = ? ' for field in self.fields])


class SQLBasicDelete(SQLBasicBuilder):

    def __init__(self, target_table=None, operation=''):
        super().__init__('DELETE', target_table)

    @property
    def query(self):
        compiled_query = super().query
        compiled_query += 'from ' + self.target_model.table_name + ' '
        compiled_query = self.get_conditions_query(compiled_query)
        return compiled_query


class SQLBasicSelect(SQLBasicBuilder):
    def __init__(self, target_table, fields):
        super().__init__('SELECT', target_table, fields)
        self.sort_field = None
        self.sort_order = None

    @property
    def left_joins(self):
        return (field for field in self.target_model.fields if isinstance(field, ForeignKeyField))

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

        compiled_query += self.get_conditions_query()
        return compiled_query


class SQLLogSelect(SQLBasicSelect):
    def get_conditions_query(self, query):
        query = super().get_conditions_query(query)
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
            self.params.append(page_size * (page - 1))
            self.params.append(page_size)

    def get_offset_query(self):
        query = ''
        if self.pagination:
            query = 'OFFSET ? ROWS FETCH FIRST ? ROWS ONLY '
            page = self.pagination[0]
            page_size = self.pagination[1]

            self.params.append(page_size*(page-1))
            self.params.append(page_size)
        return query

    # def get_order_by_query(self):
    #     query = ''
    #     if self.sort_field is not None and 0 <= self.sort_field < len(self.fields):
    #         query += 'ORDER BY ' + self.fields[self.sort_field] + ' '
    #
    #         if self.sort_order:
    #             query += self.sort_order + ' '
    #     return query

    @property
    def query(self):
        compiled_query = super().query
        # compiled_query += self.get_order_by_query(compiled_query)
        compiled_query += self.get_offset_query()
        return compiled_query
