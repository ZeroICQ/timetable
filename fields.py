class BaseField:
    def __init__(self, title=None, width=10):
        self.title = title
        self.width = width

    def get_title(self):
        return self.title


class IntegerField(BaseField):
    def __init__(self, title=None, width=10):
        super().__init__(title, width)


class PKField(IntegerField):
    def __init__(self, title=None, width=10):
        if title is None:
            title = 'ID'
        super().__init__(title, width)

    def mem(self):
        print('mem')


class StringField(BaseField):
    def __init__(self, title=None, width=50):
        super().__init__(title, width)
