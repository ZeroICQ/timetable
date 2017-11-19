class SQLBuilder:
    def __init__(self, operation=''):
        self.operation = operation
        self.fields = []
        self.pagination = ()
        self.params = []
        self.eq_wheres = []

    @property
    def query(self):
        return self.operation + ' '

    def add_param_eq_where(self, field_no, val):
        self.eq_wheres.append(field_no)
        self.params.append(val)

    def execute(self, cur):
        return cur.execute(self.query, (self.params + list(self.pagination)))


class SQLCountAll(SQLBuilder):
    def __init__(self, target_table):
        super().__init__('SELECT ')

        self.left_joins = []
        self.from_table = target_table

    def add_selected_fields(self, query):
        return query + 'COUNT(*) '



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
            compiled_query  += 'LEFT JOIN {0} on {3}.{1}={0}.{2} '.format(field.target_table, field.col_name, field.target_pk, self.from_table.table_name)

        for param_criteria in self.eq_wheres:
            if 0 <= param_criteria < len(self.fields):
                compiled_query += "WHERE {0} = ? ".format(self.fields[param_criteria])

        # if self.pagination:
        #     compiled_query += 'OFFSET ? ROWS FETCH FIRST ? ROWS ONLY '

        return compiled_query


class SQLSelect(SQLCountAll):
    def add_offset_fetch(self, query):
        if self.pagination:
            query += 'OFFSET ? ROWS FETCH FIRST ? ROWS ONLY '
        return query

    def add_selected_fields(self, query):
        first = True
        for field in self.fields:
            if first:
                first = False
            else:
                query += ', '
            query += field

        query += ' '
        return query

    @property
    def query(self):
        compiled_query = super().query
        compiled_query = self.add_offset_fetch(compiled_query)
        return compiled_query
