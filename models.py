import flask
import fdb
from fields import BaseField, IntegerField, StringField, PKField, ForeignKeyField
from sqlbuilder import SQLSelect


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(flask.g, 'fb_db'):
        flask.g.fb_db = fdb.connect(
            dsn='db/TIMETABLE.FDB',
            user='SYSDBA',
            password='masterkey',
            connection_class=fdb.ConnectionWithSchema,
            charset='UTF8'
        )
    return flask.g.fb_db


def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(flask.g, 'fb_db'):
        flask.g.fb_db.close()


class BaseModel:
    title = None

    def __init__(self,):
        self.table_name = None

    def get_cols(self):
        return [val for attr, val in self.__dict__.items() if isinstance(val, BaseField)]

    def get_titles(self):
        titles = []
        for attr in self.get_cols():
            title = attr.get_title()
            if isinstance(title, (list, tuple)):
                for el in title:
                    titles.append(el)
            else:
                titles.append(title)

        return titles
        # return [attr.get_title() for attr in self.get_cols()]

    def get_table_name(self):
        return self.table_name

    @classmethod
    def get_title(cls):
        return cls.title

    def fetch_all(self):
        cur = get_db().cursor()

        colls = self.get_cols()

        last = len(colls) - 1

        sql = SQLSelect(from_table=self.table_name)

        for col in self.get_cols():
            col.select_col(sql)

        cur.execute(sql.get_query())
        return cur.fetchall()


class AudienceModel(BaseModel):
    title = 'Аудитории'

    def __init__(self):
        super().__init__()
        self.table_name = 'AUDIENCES'
        self.pk = PKField()
        self.name = StringField(title='Номер', col_name='name')


class GroupsModel(BaseModel):
    title = 'Группы'

    def __init__(self):
        super().__init__()
        self.table_name = 'GROUPS'
        self.pk = PKField()
        self.name = StringField(title='Группа', col_name='name')



class SubjectsModel(BaseModel):
    title = 'Предметы'

    def __init__(self):
        super().__init__()
        self.table_name = 'SUBJECTS'
        self.pk = PKField()
        self.name = StringField(title='Предмет', col_name='name')



class SubjectGroupModel(BaseModel):
    title = 'Группа - предмет'

    def __init__(self):
        super().__init__()
        self.table_name='SUBJECT_GROUP'
        self.subject = ForeignKeyField('Предмет', col_name='subject_id', target_table='subjects', target_fields=['name'], target_fields_titles=['Название предмета'])
        self.groups = ForeignKeyField('Группа', col_name='group_id', target_table='groups', target_fields=['name'], target_fields_titles=['Название группы'])


# a = AudienceModel()
# print(a.__dict__)
# print(a.get_titles())