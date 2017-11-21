import flask
import fdb
from fields import BaseField, IntegerField, StringField, PKField, ForeignKeyField
from sqlbuilder import SQLSelect, SQLCountAll
from math import ceil

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


def get_cursor():
    if not hasattr(flask.g, 'fb_cur'):
        flask.g.fb_cur = get_db().cursor()
    return flask.g.fb_cur


def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(flask.g, 'fb_db'):
        flask.g.fb_db.close()


class BaseModel:
    title = None

    def __init__(self):
        self.table_name = None
        self.pagination = None

    @property
    def fields(self):
        return [val for attr, val in self.__dict__.items() if isinstance(val, BaseField)]

    @property
    def fields_titles(self):
        titles = []
        for field in self.fields:
            title = field.title

            if isinstance(title, (list, tuple)):
                for el in title:
                    titles.append(el)
            else:
                titles.append(title)

        return titles

    def get_pages(self, fields=None, values=None):
        cur = get_cursor()
        sql = SQLCountAll(self)
        self.select_all(sql)
        self.add_criteria(fields, values, sql)

        sql.execute(cur)
        rows = cur.fetchone()[0]

        if self.pagination:
            on_page = self.pagination[1]
        else:
            on_page = rows

        return ceil(rows/on_page)

    def select_all(self, sql=None):
        if sql is None:
            sql = SQLSelect(target_table=self)

        if self.pagination is not None:
            sql.pagination = self.pagination

        for field in self.fields:
            field.select_col(sql)
        return sql

    def fetch_all(self):
        cur = get_cursor()
        sql = self.select_all()
        sql.execute(cur)
        return cur.fetchall()

    def add_criteria(self, fields, vals, logic_operators, compare_operators, sql):
        if not fields or not vals:
            return

        if len(fields) == len(vals):
            for param in zip(fields, vals):
                if param[1]:
                    sql.add_param_eq_where(param[0], param[1])

    def fetch_all_by_criteria(self, fields, vals, logic_operators, compare_operators):
        cur = get_cursor()
        sql = self.select_all()
        self.add_criteria(fields, vals, logic_operators, compare_operators,sql)
        sql.execute(cur)
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
        self.lesson = ForeignKeyField(col_name='lesson_id', target_table='lessons', target_fields=(('name', 'Пара'),))
        self.subject = ForeignKeyField(col_name='subject_id', target_table='subjects', target_fields=(('name', 'Предмет'),))
        self.audience = ForeignKeyField(col_name='audience_id', target_table='audiences', target_fields=(('name', 'Аудитория'),))
        self.group = ForeignKeyField(col_name='group_id', target_table='groups', target_fields=(('name', 'Группа'),))
        self.teacher = ForeignKeyField(col_name='teacher_id', target_table='teachers', target_fields=(('name', 'ФИО Преподавателя'),))
        self.type = ForeignKeyField(col_name='type_id', target_table='lesson_types', target_fields=(('name', 'Тип'),))
        self.weekday = ForeignKeyField(col_name='weekday_id', target_table='weekdays', target_fields=(('name', 'День недели'),))


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
        self.subject = ForeignKeyField(col_name='subject_id', target_table='subjects', target_fields=(('name', 'Название предмета'),))
        self.groups = ForeignKeyField(col_name='group_id', target_table='groups', target_fields=(('name','Название группы'),))


class SubjectTeacherModel(BaseModel):
    title = 'Нагрузка учителя'

    def __init__(self):
        super().__init__()
        self.table_name = 'subject_teacher'
        self.subject = ForeignKeyField(col_name='subject_id', target_table='subjects', target_fields=(('name', 'Название предмета'),))
        self.teacher = ForeignKeyField(col_name='teacher_id', target_table='teachers', target_fields=(('name', 'ФИО Преподавателя'),))


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
