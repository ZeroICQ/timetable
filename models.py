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


class LessonsModel(BaseModel):
    title = 'Пары'

    def __init__(self):
        super().__init__()
        self.table_name = 'LESSONS'
        self.pk = PKField()
        self.name = StringField(title='Название', col_name='name')
        self.order_number = IntegerField(title='Порядковый номер', col_name='order_number')

class LessonTypesModel(BaseModel):
    title = 'Тип пары'

    def __init__(self):
        super().__init__()
        self.table_name = 'lesson_types'
        self.pk = PKField()
        self.name = StringField(title='Название', col_name='name')


class SchedItemsModel(BaseModel):
    title = 'Расписание'

    def __init__(self):
        super().__init__()
        self.table_name = 'sched_items'
        self.pk = PKField()
        self.lesson = ForeignKeyField(col_name='lesson_id', target_table='lessons',
                                      target_fields=['name'], target_fields_titles=['Пара'])
        self.subject = ForeignKeyField(col_name='subject_id', target_table='subjects',
                                       target_fields=['name'], target_fields_titles=['Предмет'])
        self.audience = ForeignKeyField(col_name='audience_id', target_table='audiences',
                                        target_fields=['name'], target_fields_titles=['Аудитория'])
        self.group = ForeignKeyField(col_name='group_id', target_table='groups',
                                     target_fields=['name'], target_fields_titles=['Группа'])
        self.teacher = ForeignKeyField(col_name='teacher_id', target_table='teachers',
                                       target_fields=['name'], target_fields_titles=['ФИО Преподавателя'])
        self.type = ForeignKeyField(col_name='type_id', target_table='lesson_types',
                                    target_fields=['name'], target_fields_titles=['Тип'])
        self.weekday = ForeignKeyField(col_name='weekday_id', target_table='weekdays',
                                       target_fields=['name'], target_fields_titles=['День недели'])


class SubjectsModel(BaseModel):
    title = 'Предметы'

    def __init__(self):
        super().__init__()
        self.table_name = 'SUBJECTS'
        self.pk = PKField()
        self.name = StringField(title='Предмет', col_name='name')


class SubjectGroupModel(BaseModel):
    title = 'Учебный план'

    def __init__(self):
        super().__init__()
        self.table_name = 'SUBJECT_GROUP'
        self.subject = ForeignKeyField(col_name='subject_id', target_table='subjects',
                                       target_fields=['name'], target_fields_titles=['Название предмета'])
        self.groups = ForeignKeyField(col_name='group_id', target_table='groups',
                                      target_fields=['name'], target_fields_titles=['Название группы'])

class SubjectTeacherModel(BaseModel):
    title = 'Нагрузка учителя'

    def __init__(self):
        super().__init__()
        self.table_name = 'subject_teacher'
        self.subject = ForeignKeyField(col_name='subject_id', target_table='subjects',
                                       target_fields=['name'], target_fields_titles=['Название предмета'])
        self.teacher = ForeignKeyField(col_name='teacher_id', target_table='teachers',
                                       target_fields=['name'], target_fields_titles=['ФИО Преподавателя'])

class TeachersModel(BaseModel):
    title = 'Учителя'

    def __init__(self):
        super().__init__()
        self.table_name = 'teachers'
        self.id = PKField()
        self.name = StringField('ФИО', col_name='name')


class WeekdaysModel(BaseModel):
    title = 'Дни недели'

    def __init__(self):
        super().__init__()
        self.table_name = 'weekdays'
        self.id = PKField()
        self.name = StringField('Название', col_name='name')
        self.order_number = IntegerField('Порядковый номер', col_name='order_number')
