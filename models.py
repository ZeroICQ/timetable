from fields import BaseField, IntegerField, StringField, PKField
from managers import BaseManager


class BaseModel:
    def __init__(self):
        self.table_name = None
        self.manager = BaseManager

        self._manager_instance = None

    def get_fields(self):
        return [val for attr, val in self.__dict__.items() if isinstance(val, BaseField)]

    def get_titles(self):
        return [attr.get_title() for attr in self.get_fields()]

    def get_table_name(self):
        return self.table_name

    def get_manager(self):
        if self._manager_instance is None:
            self._manager_instance = self.manager(self.table_name)

        return self._manager_instance


class AudienceModel(BaseModel):
    def __init__(self):
        super().__init__()
        self.table_name = 'AUDIENCES'

        self.pk = PKField()
        self.name = StringField(title='Номер')

#
# a = AudienceModel()
# print(a.__dict__)
# print(a.get_titles())