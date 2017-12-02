from conditions import CustomCondition


class SQLBasicBuilder:
    def __init__(self, operation='', target_table=None):
        self.operation = operation
        self.target_table = target_table
        self.fields = []
        self.pagination = ()
        self.conditions = []
        self.custom_conditions = []

    @property
    def query(self):
        return self.operation + ' '

    def add_where_param(self, cond):
        self.conditions.append(cond)

    def add_custom_where_param(self, cond):
        self.custom_conditions.append(cond)

    def add_where_equal_param(self, col_name, val, logic_operator=None):
        self.custom_conditions.append(CustomCondition(col_name, val, '=', logic_operator=logic_operator))

    def add_selected_fields(self, query):
        return query + ', '.join(self.fields) + ' '

    def execute(self, cur, params=None):
        if params is None:
            params = []
        params += [cond.val for cond in self.conditions]
        params += [cond.val for cond in self.custom_conditions]
        return cur.execute(self.query, (params + list(self.pagination)))

    def add_selected_conditions(self, query):
        if self.conditions or self.custom_conditions:
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

        first = True
        for cond in self.custom_conditions:
            if first:
                first = False
            else:
                query += cond.logic_operator + ' '

            query += '{table_name}.{field_name} {operator} ? '.format(
                table_name=self.target_table.table_name,
                field_name=cond.field_name,
                operator=cond.compare_operator)
        return query


class SQLBasicUpdate(SQLBasicBuilder):
    def __init__(self, target_table, values=None):
        super().__init__('UPDATE', target_table)
        self.values = values

    def execute(self, cur, params=None):
        if params is None:
            params = []
        params += self.values
        return super().execute(cur, params)

    @property
    def query(self):
        compiled_query = super().query
        compiled_query += self.target_table.table_name + ' SET '
        compiled_query = self.add_updating_fields(compiled_query)
        compiled_query = self.add_selected_conditions(compiled_query)

        return compiled_query

    def add_field(self, field):
        self.fields.append(field)

    def add_updating_fields(self, query):
        return query + ', '.join([field + ' = ? ' for field in self.fields])


class SQLBasicSelect(SQLBasicBuilder):
    def __init__(self, target_table):
        super().__init__('SELECT', target_table)
        self.left_joins = []
        self.sort_field = None
        self.sort_order = None

    def add_field(self, field, table=None):
        if table is None:
            table = self.target_table.table_name

        col_name = table + '.' + field
        self.fields.append(col_name)

    def add_left_join(self, field):
        self.left_joins.append(field)

    @property
    def query(self):
        compiled_query = super().query
        compiled_query = self.add_selected_fields(compiled_query)
        compiled_query += 'from ' + self.target_table.table_name + ' '
        for field in self.left_joins:
            compiled_query += 'LEFT JOIN {target_table} on {from_table}.{col_name}={target_table}.{target_pk} '.format(
                target_table=field.target_table,
                col_name=field.col_name,
                target_pk=field.target_pk,
                from_table=self.target_table.table_name
            )

        compiled_query = self.add_selected_conditions(compiled_query)
        # if self.conditions or self.custom_conditions:
        #     compiled_query += "WHERE "
        # first = True
        # for cond in self.conditions:
        #     if not (0 <= cond.field < len(self.fields)):
        #         continue
        #
        #     if first:
        #         first = False
        #     else:
        #         compiled_query += cond.logic_operator + ' '
        #
        #     compiled_query += '{0} {1} ? '.format(self.fields[cond.field], cond.compare_operator)
        #
        # first = True
        # for cond in self.custom_conditions:
        #     if first:
        #         first = False
        #     else:
        #         compiled_query += cond.logic_operator + ' '
        #
        #     compiled_query += '{table_name}.{field_name} {operator} ? '.format(
        #         table_name=self.target_table.table_name,
        #         field_name=cond.field_name,
        #         operator=cond.compare_operator)

        return compiled_query


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
