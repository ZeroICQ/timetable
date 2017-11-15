class BaseField:
    def __init__(self, title=None, width=10, coll_name=None):
        self.title = title
        self.width = width
        self.coll_name = coll_name

    def get_title(self):
        return self.title

    def select_coll(self):
        return self.coll_name


class IntegerField(BaseField):
    def __init__(self, title=None, width=10, coll_name=None):
        super().__init__(title, width)
        self.coll_name = coll_name


class PKField(IntegerField):
    def __init__(self, title='ID', width=10, coll_name='ID'):
        super().__init__(title, width, coll_name)


class ForeignKeyField(BaseField):
    def __init__(self, title=None, width=10, coll_name=None, target_table=None, target_fields=[], target_pk='id'):
        super().__init__(title, width, coll_name)
        self.target_pk = target_pk
        self.target_fields = target_fields
        self.target_table = target_table

    def select_coll(self):
        for tgr in self.target_fields
        return self.target_table +


class StringField(BaseField):
    def __init__(self, title=None, width=50, coll_name=None):
        super().__init__(title, width, coll_name)
