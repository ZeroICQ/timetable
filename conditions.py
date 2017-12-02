class BasicCondition:
    compare_operators = ('=', '!=', '>', '>=', '<', '<=', 'LIKE')
    logic_operators = ['AND', 'OR']

    def __init__(self, field, val, logic_operator, compare_operator):
        super().__init__()
        self._logic_operator = 0
        self._compare_operator = 0
        self.field = field
        self.val = val
        self.logic_operator = logic_operator if 0 <= logic_operator < len(self.logic_operators) else 0
        self.compare_operator = compare_operator if 0 <= compare_operator < len(self.compare_operators) else 0

    @property
    def logic_operator(self):
        return self.logic_operators[self._logic_operator]

    @logic_operator.setter
    def logic_operator(self, val):
        self._logic_operator = val

    @property
    def compare_operator(self):
        return self.compare_operators[self._compare_operator]

    @compare_operator.setter
    def compare_operator(self, val):
        self._compare_operator = val


class CustomCondition():
    def __init__(self, field_name, val, compare_operator, logic_operator='AND'):
        self.field_name = field_name
        self.val = val
        self.compare_operator = compare_operator
        self.logic_operator = logic_operator
