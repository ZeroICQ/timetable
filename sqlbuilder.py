from conditions import CustomCondition
import weakref


class SQLBasicBuilder:
    def __init__(self, operation='', target_table=None):
        self.operation = operation
        self.target_table = weakref.ref(target_table)
        self.fields = []
        self.pagination = ()
        self.conditions = []
        self.custom_conditions = []
        self.group_conditions = []

    @property
    def query(self):
        return self.operation + ' '

    def add_condition(self, cond):
        self.conditions.append(cond)

    def add_custom_condition(self, cond):
        self.custom_conditions.append(cond)

    def add_group_condition(self, cond):
        self.group_conditions.append(cond)

    def add_where_equal_param(self, col_name, val, logic_operator=None):
        self.custom_conditions.append(CustomCondition(col_name, val, '=', logic_operator=logic_operator))

    def add_selected_fields(self, query):
        return query + ', '.join(self.fields) + ' '

    def execute(self, cur, params=None):
        if params is None:
            params = []
        params += [cond.val for cond in self.conditions]
        params += [cond.val for cond in self.custom_conditions]
        params += [cond.val for group in self.group_conditions for cond in group.conditions]
        return cur.execute(self.query, (params + list(self.pagination)))

    def add_selected_custom_conditions(self, query, conditions):
        first = True
        for cond in conditions:
            if first:
                first = False
            else:
                query += cond.logic_operator + ' '

            query += '{table_name}.{field_name} {operator} ? '.format(
                table_name=self.target_table().table_name,
                field_name=cond.field_name,
                operator=cond.compare_operator)

        return query

    def add_selected_group(self, query, conditions):
        query += '('
        query = self.add_selected_custom_conditions(query, conditions)
        query += ') '
        return query

    def add_selected_conditions(self, query):
        if self.conditions or self.custom_conditions or self.group_conditions:
            query += "WHERE "

        first = True
        for cond in self.conditions:
            if not (0 <= cond.field < len(self.fields)):
                continue

            if first:
                first = False
            else:
                query += cond.logic_operator + ' '

            query += '{0} {1} ? '.format(self.fields[cond.field], cond.compare_operator)

        query = self.add_selected_custom_conditions(query, self.custom_conditions)

        first = not self.custom_conditions

        for group in self.group_conditions:
            if first:
                first = False
            else:
                query += group.logic_operator + ' '

            query = self.add_selected_group(query, group.conditions)

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
        compiled_query += 'INTO ' + self.target_table().table_name + ' '
        compiled_query = self.add_inserting_fields(compiled_query)
        compiled_query += ' RETURNING ' + self.target_table().pk.col_name
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
        compiled_query = self.operation + ' ' + self.target_table().table_name + ' SET '
        compiled_query = self.add_updating_fields(compiled_query)
        compiled_query = self.add_selected_conditions(compiled_query)
        compiled_query += ' RETURNING ' + self.target_table().pk.col_name

        return compiled_query

    def add_updating_fields(self, query):
        return query + ', '.join([field + ' = ? ' for field in self.fields])


class SQLBasicDelete(SQLBasicBuilder):

    def __init__(self, target_table=None, operation=''):
        super().__init__('DELETE', target_table)

    @property
    def query(self):
        compiled_query = super().query
        compiled_query += 'from ' + self.target_table().table_name + ' '
        compiled_query = self.add_selected_conditions(compiled_query)
        return compiled_query


class SQLBasicSelect(SQLBasicBuilder):
    def __init__(self, target_table):
        super().__init__('SELECT', target_table)
        self.left_joins = []
        self.sort_field = None
        self.sort_order = None

    def add_field(self, field, table=None):
        if table is None:
            table = self.target_table().table_name

        col_name = table + '.' + field
        self.fields.append(col_name)

    def add_left_join(self, field):
        self.left_joins.append(field)

    @property
    def query(self):
        compiled_query = super().query
        compiled_query = self.add_selected_fields(compiled_query)
        compiled_query += 'from ' + self.target_table().table_name + ' '
        for field in self.left_joins:
            compiled_query += 'LEFT JOIN {target_table} on {from_table}.{col_name}={target_table}.{target_pk} '.format(
                target_table=field.target_table,
                col_name=field.col_name,
                target_pk=field.target_pk,
                from_table=self.target_table().table_name
            )

        compiled_query = self.add_selected_conditions(compiled_query)
        return compiled_query


class SQLLogSelect(SQLBasicSelect):
    def add_selected_conditions(self, query):
        query = super().add_selected_conditions(query)
        subselect = 'AND {table_name}.{time_col_name} = (select max({tmp_table_name}.{time_col_name}) from {table_name} {tmp_table_name} ' \
                    'where {tmp_table_name}.{table_pk} = {table_name}.{table_pk}) '.format(
                        tmp_table_name=self.target_table().table_name + '1',
                        time_col_name=self.target_table().datetime.col_name,
                        table_name=self.target_table().table_name,
                        table_pk=self.target_table().logged_table_pk.col_name)

        query += subselect
        return query


class SQLCountAll(SQLBasicSelect):
    def add_selected_fields(self, query):
        return query + 'COUNT(*) '


class SQLSelect(SQLBasicSelect):
    def add_offset_fetch(self, query):
        if self.pagination:
            query += 'OFFSET ? ROWS FETCH FIRST ? ROWS ONLY '
        return query

    def add_sort(self, query):
        if self.sort_field is not None and 0 <= self.sort_field < len(self.fields):
            query += 'ORDER BY ' + self.fields[self.sort_field] + ' '

            if self.sort_order:
                query += self.sort_order + ' '
        return query

    @property
    def query(self):
        compiled_query = super().query
        compiled_query = self.add_sort(compiled_query)
        compiled_query = self.add_offset_fetch(compiled_query)
        return compiled_query
