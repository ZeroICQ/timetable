from fields import BaseField, IntegerField, StringField, PKField


class BaseModel:
    def __init__(self):
        self.table_name = None
        self.manager = 'BaseManager'

    def get_colls(self):
        return [val for attr, val in self.__dict__.items() if isinstance(val, BaseField)]

    def get_titles(self):
        return [attr.get_title() for attr in self.get_colls()]

    def get_table_name(self):
        return self.table_name

    def get_manager(self):
        return self.manager


class AudienceModel(BaseModel):
    def __init__(self):
        super().__init__()
        self.table_name = 'AUDIENCES'

        self.pk = PKField()
        self.name = StringField(title='Номер', coll_name='name')

#
# a = AudienceModel()
# print(a.__dict__)
# print(a.get_titles())