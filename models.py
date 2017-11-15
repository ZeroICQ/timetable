from fields import IntegerField, StringField

class BaseModel():
    def __init__(self):
        self.table_name = None


class AudienceModel(BaseModel):
    def __init__(self):
        table_name = 'AUDIENCES'
        id = IntegerField()
        name = StringField()
