class SQLBuilder:
    def __init__(self, operation=''):
        self.operation = operation
        self.cols = []

class SQLSelect(SQLBuilder):
    def __init__(self, from_table):
        super().__init__('SELECT')
        self.left_joins = []
        self.from_table = from_table
        self.query = 'SELECT '

    def add_enum(self, enum):
        first = True
        for elem in enum:
            if first:
                first = False
            else:
                self.query += ', '
            self.query += elem

        self.query += ' '

    def add_col(self, coll_name, table=None):
        if table is None:
            table= self.from_table

        coll_name = table + '.' + coll_name
        self.cols.append(coll_name)

    def add_left_join(self,  table_name, col_name, target_pk, col_pk='id'):
        self.left_joins.append({'table_name': table_name, 'col_name': col_name, 'target_pk': target_pk, 'col_pk': col_pk})

    def get_query(self):
        print('----------------------------------')
        print(self.from_table)
        last = len(self.cols) - 1
        print(self.cols)
        self.add_enum(self.cols)
        # for i, col in enumerate(self.cols):
        #     query += col
        #     if i != last:
        #         query += ','
        #     query += ' '

        self.query += 'from ' + self.from_table + ' '

        first = True
        print('--------------------')
        print(self.left_joins)
        for join in self.left_joins:
            self.query += 'LEFT JOIN {0} on {3}.{1}={0}.{2}'.format(join['table_name'], join['col_name'], join['target_pk'], self.from_table, join['col_pk']) + ' '
        print(self.query)
        return self.query
