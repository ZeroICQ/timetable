class BasicCondition:
    compare_operators = ('=', '!=', '>', '>=', '<', '<=', 'LIKE')
    logic_operators = ['AND', 'OR']

    def __init__(self, field_name, value=None, compare_operator=None, logic_operator='AND'):
        super().__init__()

        self.field_name = field_name
        self._value = value
        self.logic_operator = logic_operator
        self.compare_operator = compare_operator

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def get_query_str(self, include_logic_operator=True):
        query = self.logic_operator + ' ' if include_logic_operator else ''
        query += '{field_name} {cmp_op} ? '.format(field_name=self.field_name, cmp_op=self.compare_operator)
        return query

    def add_values(self, params:list):
        params.append(self.value)


class BetweenCondition(BasicCondition):
    def __init__(self, field_name, value_l, value_r, logic_operator='AND'):
        super().__init__(field_name, logic_operator=logic_operator)
        self.value_l = value_l
        self.value_r = value_r

    @property
    def value(self):
        return self.value_l, self.value_r

    def get_query_str(self, include_logic_operator=True):
        query = self.logic_operator + ' ' if include_logic_operator else ''
        query += '(? <  {field_name} and {field_name} < ?) '.format(field_name=self.field_name)
        return query

    def add_values(self, params:list):
        params.append(self.value_l)
        params.append(self.value_r)


def create_conditions(field_names, values, compare_operators, logic_operators):
    return [condition for condition in map(BasicCondition, field_names, values, compare_operators, logic_operators)]

# TODO: delete
# class CustomCondition:
#     def __init__(self, field_name, val, compare_operator, logic_operator='AND'):
#         self.field_name = field_name
#         self.val = val
#         self.compare_operator = compare_operator
#         self.logic_operator = logic_operator

#
# class GroupCondition():
#     def __init__(self, logic_operator):
#         self.logic_operator = logic_operator
#         self.conditions = []
#
#     def add_condition(self, condition):
#         self.conditions.append(condition)