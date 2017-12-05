import flask
import fdb
from fields import BaseField, IntegerField, StringField, PKField, ForeignKeyField, TimestampField
from sqlbuilder import SQLSelect, SQLCountAll, SQLBasicUpdate, SQLBasicDelete, SQLBasicInsert, SQLLog
from math import ceil
from conditions import BasicCondition, CustomCondition
from datetime import datetime

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
    # if not hasattr(flask.g, 'fb_cur'):
    #     flask.g.fb_cur = get_db().cursor()
    # return flask.g.fb_cur
    return get_db().cursor()


def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(flask.g, 'fb_db'):
        flask.g.fb_db.close()


class BasicModel:
    title = None

    def __init__(self):
        self.table_name = None
        self.pagination = None
        self.pk = PKField()

    @property
    def fields(self):
        return [val for attr, val in self.__dict__.items() if isinstance(val, BaseField)]

    @property
    def mutable_fields(self):
        return [val for attr, val in self.__dict__.items() if isinstance(val, BaseField) and not isinstance(val, PKField)]

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

    def get_pages(self, fields=None, values=None, logic_operators=None, compare_operators=None):
        cur = get_cursor()
        sql = SQLCountAll(self)
        self.select_all_fields(sql)
        self.add_criteria(fields, values, logic_operators, compare_operators, sql)

        sql.execute(cur)
        rows = cur.fetchone()[0]

        if self.pagination:
            on_page = self.pagination[1]
        else:
            on_page = rows

        return ceil(rows/on_page)

    def select_all_fields(self, sql=None):
        if sql is None:
            sql = SQLSelect(target_table=self)

        if self.pagination is not None:
            sql.pagination = self.pagination

        for field in self.fields:
            field.select_col(sql)
        return sql

    def select_all_fields_raw(self, sql=None):
        if sql is None:
            sql = SQLSelect(target_table=self)

        if self.pagination is not None:
            sql.pagination = self.pagination

        for field in self.mutable_fields:
            field.select_col_raw(sql)
        return sql

    def fetch_all(self, sort_field, sort_order):
        cur = get_cursor()
        sql = self.select_all_fields()
        sql.sort_field = sort_field
        sql.sort_order = sort_order
        sql.execute(cur)
        return cur.fetchall()

    def add_criteria(self, fields, vals, logic_operators, compare_operators, sql):
        if not fields or not vals:
            return

        if len(fields) == len(vals):
            for param in zip(fields, vals, logic_operators, compare_operators):
                if param[1]:
                    sql.add_where_param(BasicCondition(param[0], param[1], param[2], param[3]))

    def fetch_all_by_criteria(self, fields, vals, logic_operators, compare_operators, sort_field, sort_order):
        cur = get_cursor()
        sql = self.select_all_fields()
        self.add_criteria(fields, vals, logic_operators, compare_operators, sql)
        sql.sort_field = sort_field
        sql.sort_order = sort_order
        sql.execute(cur)
        return cur.fetchall()

    def fetch_raw_by_pk(self, pk_val):
        cur = get_cursor()
        sql = self.select_all_fields_raw()
        sql.add_where_equal_param(self.pk.col_name, pk_val)
        sql.execute(cur)
        return cur.fetchone()

    def log_action(self, cursor, action, pk):
        actions = {'delete': 1,
                   'modify': 2}

        log_table = LogModel()
        log_sql = SQLLog(target_table=log_table, values=[actions[action], self.table_name, pk])
        log_sql.execute(cursor)

    def update(self, fields, values, pk_val):
        cur = get_cursor()
        sql = SQLBasicUpdate(self, values)
        sql = self.select_all_fields_raw(sql)
        sql.add_where_equal_param(self.pk.col_name, pk_val)
        sql.execute(cur)
        pk = cur.fetchone()[0]

        self.log_action(cursor=cur, pk=pk, action='modify')
        cur.transaction.commit()
        return pk

    def delete_by_id(self, pk_val):
        cur = get_cursor()
        sql = SQLBasicDelete(self)
        sql.add_where_equal_param(self.pk.col_name, pk_val)
        sql.execute(cur)
        self.log_action(cursor=cur, pk=pk_val, action='delete')
        cur.transaction.commit()

    def insert(self, values):
        cur = get_cursor()
        sql = SQLBasicInsert(self, values=values)
        sql = self.select_all_fields_raw(sql)
        sql.execute(cur)
        pk = cur.fetchone()[0]
        cur.transaction.commit()
        return pk


class AudienceModel(BasicModel):
    title = 'Аудитории'

    def __init__(self):
        super().__init__()
        self.table_name = 'AUDIENCES'
        self.name = StringField(title='Номер', col_name='name')


class GroupsModel(BasicModel):
    title = 'Группы'

    def __init__(self):
        super().__init__()
        self.table_name = 'GROUPS'
        self.name = StringField(title='Группа', col_name='name')


class LessonsModel(BasicModel):
    title = 'Пары'

    def __init__(self):
        super().__init__()
        self.table_name = 'LESSONS'
        self.name = StringField(title='Название', col_name='name')
        self.order_number = IntegerField(title='Порядковый номер', col_name='order_number')


class LessonTypesModel(BasicModel):
    title = 'Тип пары'

    def __init__(self):
        super().__init__()
        self.table_name = 'lesson_types'
        self.name = StringField(title='Название', col_name='name')


class SchedItemsModel(BasicModel):
    title = 'Расписание'

    def __init__(self):
        super().__init__()
        self.table_name = 'sched_items'
        self.lesson = ForeignKeyField(col_name='lesson_id', target_table='lessons', target_fields=(('name', 'Пара'),), target_title='Предмет')
        self.subject = ForeignKeyField(col_name='subject_id', target_table='subjects', target_fields=(('name', 'Предмет'),))
        self.audience = ForeignKeyField(col_name='audience_id', target_table='audiences', target_fields=(('name', 'Аудитория'),))
        self.group = ForeignKeyField(col_name='group_id', target_table='groups', target_fields=(('name', 'Группа'),))
        self.teacher = ForeignKeyField(col_name='teacher_id', target_table='teachers', target_fields=(('name', 'ФИО Преподавателя'),))
        self.type = ForeignKeyField(col_name='type_id', target_table='lesson_types', target_fields=(('name', 'Тип'),))
        self.weekday = ForeignKeyField(col_name='weekday_id', target_table='weekdays', target_fields=(('name', 'День недели'),))


class SubjectsModel(BasicModel):
    title = 'Предметы'

    def __init__(self):
        super().__init__()
        self.table_name = 'SUBJECTS'
        self.name = StringField(title='Предмет', col_name='name')


class SubjectGroupModel(BasicModel):
    title = 'Учебный план'

    def __init__(self):
        super().__init__()
        self.table_name = 'SUBJECT_GROUP'
        self.subject = ForeignKeyField(col_name='subject_id', target_table='subjects', target_fields=(('name', 'Название предмета'),))
        self.groups = ForeignKeyField(col_name='group_id', target_table='groups', target_fields=(('name','Название группы'),))


class SubjectTeacherModel(BasicModel):
    title = 'Нагрузка учителя'

    def __init__(self):
        super().__init__()
        self.table_name = 'subject_teacher'
        self.subject = ForeignKeyField(col_name='subject_id', target_table='subjects', target_fields=(('name', 'Название предмета'),))
        self.teacher = ForeignKeyField(col_name='teacher_id', target_table='teachers', target_fields=(('name', 'ФИО Преподавателя'),))


class TeachersModel(BasicModel):
    title = 'Учителя'

    def __init__(self):
        super().__init__()
        self.table_name = 'teachers'
        self.name = StringField('ФИО', col_name='name')


class WeekdaysModel(BasicModel):
    title = 'Дни недели'

    def __init__(self):
        super().__init__()
        self.table_name = 'weekdays'
        self.name = StringField('Название', col_name='name')
        self.order_number = IntegerField('Порядковый номер', col_name='order_number')


class LogStatusModel(BasicModel):
    title = 'Статус записи'

    def __init__(self):
        super().__init__()
        self.table_name = 'log_status'
        self.name = StringField('Статус', col_name='name')


class LogModel(BasicModel):
    title = 'Логи'

    def __init__(self):
        super().__init__()
        self.table_name = 'log'
        self.status = ForeignKeyField(col_name='status', target_table='log_status',target_fields=(('name', 'Статус'),))
        self.logged_table_name = StringField(col_name='table_name', title='Таблица')
        self.logged_table_pk = IntegerField(col_name='table_pk', title='Ключ')
        # TODO: fix creation
        self.datetime = TimestampField(col_name='change_time', title='Время')

    def get_changes(self, date_start, pks, table_name):
        cur = get_cursor()
        sql = self.select_all_fields_raw()
        sql.add_custom_where_param(CustomCondition(field_name=self.datetime.col_name, compare_operator='>', val=date_start))
        sql.add_custom_where_param(CustomCondition(field_name=self.datetime.col_name, compare_operator='<', val=datetime.now()))
        sql.add_custom_where_param(CustomCondition(field_name=self.datetime.col_name,
                                                   compare_operator='=',
                                                   val='(select max({tmp_table_name}.{time_col_name}) '
                                                       'from {table_name} {tmp_table_name} '
                                                       'where {tmp_table_name}.{table_pk} = {table_name}.{table_pk}) '.format(tmp_table_name=self.table_name + '1',
                                                                      time_col_name=self.datetime.col_name,
                                                                      table_name=self.table_name,
                                                                      table_pk=self.logged_table_pk.col_name)))
        # l.CHANGE_TIME = (select max(l1.CHANGE_TIME)
        # from LOG l1
        # where
        # l1.table_pk = l.table_pk)
        sql.add_custom_where_param(CustomCondition(field_name=self.logged_table_name.col_name,
                                                   compare_operator='=', val=table_name))
        sql.execute(cur)
        return cur.fetchall()
