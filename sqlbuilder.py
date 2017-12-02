class SQLBaseBuilder:
    def __init__(self, operation=''):
        self.operation = operation
        self.fields = []
        self.pagination = ()
        self.conditions = []

    @property
    def query(self):
        return self.operation + ' '

    def add_where_param(self, cond):
        self.conditions.append(cond)

    def execute(self, cur):
        params = [cond.val for cond in self.conditions]
        return cur.execute(self.query, (params + list(self.pagination)))


class SQLBaseSelect(SQLBaseBuilder):
    def __init__(self, target_table):
        super().__init__('SELECT ')
        self.left_joins = []
        self.from_table = target_table
        self.sort_field = None
        self.sort_order = None

    def add_selected_fields(self, query):
        return query + ', '.join(self.fields) + ' '

    def add_field(self, field, table=None):
        if table is None:
            table = self.from_table.table_name

        col_name = table + '.' + field
        self.fields.append(col_name)

    def add_left_join(self, field):
        self.left_joins.append(field)

    @property
    def query(self):
        compiled_query = super().query
        compiled_query = self.add_selected_fields(compiled_query)
        compiled_query += 'from ' + self.from_table.table_name + ' '
        for field in self.left_joins:
            compiled_query += 'LEFT JOIN {target_table} on {from_table}.{col_name}={target_table}.{target_pk} '.format(
                target_table=field.target_table,
                col_name=field.col_name,
                target_pk=field.target_pk,
                from_table=self.from_table.table_name
            )
        if self.conditions:
            compiled_query += "WHERE "

        first = True
        for cond in self.conditions:
            if not (0 <= cond.field < len(self.fields)):
                continue

            if first:
                first = False
            else:
                compiled_query += cond.logic_operator + ' '

            compiled_query += '{0} {1} ? '.format(self.fields[cond.field], cond.compare_operator)

        return compiled_query


class SQLCountAll(SQLBaseSelect):
    def add_selected_fields(self, query):
        return query + 'COUNT(*) '


class SQLSelect(SQLBaseSelect):
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
