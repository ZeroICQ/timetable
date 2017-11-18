class SQLBuilder:
    def __init__(self, operation=''):
        self.operation = operation
        self.fields = []

    @property
    def query(self):
        return self.operation + ' '


class SQLSelect(SQLBuilder):
    def __init__(self, target_table):
        super().__init__('SELECT ')

        self.left_joins = []
        self.from_table = target_table
        self.eq_wheres = []

    def add_param_eq_where(self, field_no):
        self.eq_wheres.append(field_no)

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
        return compiled_query
