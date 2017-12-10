import flask
import fdb
from fields import BaseField, IntegerField, StringField, PKField, ForeignKeyField, TimestampField
from sqlbuilder import SQLSelect, SQLCountAll, SQLBasicUpdate, SQLBasicDelete, SQLBasicInsert, SQLLogSelect
from math import ceil
from conditions import BasicCondition
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


class BasicModelMetaclass(type):
    def __call__(self, *args, **kwargs):
        model = super().__call__(*args, **kwargs)
        model._after_init_()
        return model


class BasicModel(metaclass=BasicModelMetaclass):
    title = None
    table_name = None

    actions = {'delete': 1,
                   'modify': 2}

    def __init__(self):
        super().__init__()
        self.pagination = None
        self.pk = PKField()
        self._fields = None
        self._fields_no_fk = None
        self._fields_own = None
        self._fields_main = None

    def _after_init_(self):
        self.resolve_foreign_keys()

    def resolve_foreign_keys(self):
        resolved_fields = []

        for field in self.__dict__.values():
            if isinstance(field, ForeignKeyField):
                model = field.target_model()
                for col_name, colt_title in field.target_fields:
                    foreign_field = model.get_field_by_col_name(col_name)
                    foreign_field.title = colt_title
                    resolved_fields.append(foreign_field)

            if isinstance(field, BaseField):
                field.table_name = self.table_name

        for field in resolved_fields:
            setattr(self, field.table_name + '__' + field.col_name, field)

    def get_field_by_col_name(self, col_name):
        for field in self.__dict__.values():
            if isinstance(field, BaseField) and field.col_name == col_name:
                return field

    @property
    def main_field(self):
        return self.pk

    @property
    def fields(self):
        if self._fields is None:
            self._fields = [val for attr, val in self.__dict__.items() if isinstance(val, BaseField)]
        return self._fields

    @property
    def fields_no_fk(self):
        if self._fields_no_fk is None:
            self._fields_no_fk = [field for field in self.fields if not isinstance(field, ForeignKeyField)]
        return self._fields_no_fk

    @property
    def fields_own(self):
        if self._fields_own is None:
            self._fields_own = [field for field in self.fields if field.table_name == self.table_name and not isinstance(field, PKField)]
        return self._fields_own

    @property
    def fields_main(self):
        if self._fields_main is None:
            self._fields_main = [self.pk, self.main_field]

        return self._fields_main

    def get_pages(self, fields=None, values=None, logic_operators=None, compare_operators=None, pagination=None):
        cur = get_cursor()
        sql = SQLCountAll(self)
        # self.add_criteria(fields, values, logic_operators, compare_operators, sql)
        sql.execute(cur)

        rows = cur.fetchone()[0]
        if pagination:
            on_page = pagination[1]
        else:
            on_page = rows

        return ceil(rows/on_page)

    def fetch_all(self, sort_field=None, sort_order=None, pagination=None):
        cur = get_cursor()
        sql = SQLSelect(self, self.fields_no_fk, pagination)
        sql.sort_field = sort_field
        sql.sort_order = sort_order
        sql.execute(cur)
        return cur.fetchall()

    def add_criteria(self, fields_names, values, logic_operators, compare_operators, sql):
        # TODO: Discover whether there is a better way to iterate over map
        for r in map(sql.add_condition, fields_names, values, compare_operators, logic_operators):
            pass

    def fetch_all_by_criteria(self, fields, values, logic_operators, compare_operators, sort_field=None, sort_order=None, pagination=None):
        cur = get_cursor()
        sql = SQLSelect(self, self.fields_no_fk, pagination=pagination)
        self.add_criteria(fields, values, logic_operators, compare_operators, sql)
        sql.sort_order = sort_order
        sql.sort_field = sort_field
        sql.execute(cur)
        return cur.fetchall()

    def fetch_by_pk(self, pk_val, fields=None):
        cur = get_cursor()

        if fields is None:
            fields = self.fields_own

        sql = SQLSelect(self, fields)
        sql.add_equal_condition(self.pk.qualified_col_name, pk_val)
        sql.execute(cur)
        return cur.fetchone()

    def fetch_all_main(self):
        cur = get_cursor()
        sql = SQLSelect(self, self.fields_main)
        sql.execute(cur)
        return cur.fetchall()

    # def fetch_by_pk(self, pk_val):
    #     cur = get_cursor()
    #     sql = self.select_all_fields()
    #     sql.add_where_equal_param(self.pk.col_name, pk_val)
    #     sql.execute(cur)
    #     return cur.fetchone()
    #
    def log_action(self, cursor, action, pk):
        action = self.actions[action]
        log_table = LogModel()
        fields = {
            log_table.logged_table_name.qualified_col_name: self.table_name,
            log_table.status.qualified_col_name: action,
            log_table.logged_table_pk.qualified_col_name: pk
        }
        sql = SQLBasicInsert(log_table, fields)
        sql.execute(cursor)

    def update(self, return_fields, new_fields, pk_val):
        cur = get_cursor()
        sql = SQLBasicUpdate(self, new_fields, return_fields=return_fields)
        sql.add_equal_condition(self.pk.qualified_col_name, pk_val)
        sql.execute(cur)
        result_fields = cur.fetchone()

        self.log_action(cur, 'modify', pk_val)

        cur.transaction.commit()
        return result_fields

    def delete_by_pk(self, pk_val, return_fields=None):
        cur = get_cursor()
        sql = SQLBasicDelete(self, return_fields=return_fields)
        sql.add_equal_condition(self.pk.qualified_col_name, pk_val)
        sql.execute(cur)
        result_fields = cur.fetchone()
        self.log_action(cur, 'delete', pk_val)
        cur.transaction.commit()
        return result_fields

    def insert(self, new_fields):
        cur = get_cursor()
        sql = SQLBasicInsert(self, new_fields, [self.pk])
        sql.execute(cur)
        pk = cur.fetchone()[0]
        cur.transaction.commit()
        return pk


class AudienceModel(BasicModel):
    title = 'Аудитории'
    table_name = 'audiences'

    def __init__(self):
        super().__init__()
        self.name = StringField(title='Номер', col_name='name')

    @property
    def main_field(self):
        return self.name


class GroupsModel(BasicModel):
    title = 'Группы'
    table_name = 'groups'

    def __init__(self):
        super().__init__()
        self.name = StringField(title='Группа', col_name='name')

    @property
    def main_field(self):
        return self.name


class LessonsModel(BasicModel):
    title = 'Пары'
    table_name = 'lessons'

    def __init__(self):
        super().__init__()
        self.name = StringField(title='Название', col_name='name')
        self.order_number = IntegerField(title='Порядковый номер', col_name='order_number')

    @property
    def main_field(self):
        return self.name


class LessonTypesModel(BasicModel):
    title = 'Тип пары'
    table_name = 'lesson_types'

    def __init__(self):
        super().__init__()
        self.name = StringField(title='Название', col_name='name')

    @property
    def main_field(self):
        return self.name


class SubjectsModel(BasicModel):
    title = 'Предметы'
    table_name = 'subjects'

    def __init__(self):
        super().__init__()
        self.name = StringField(title='Предмет', col_name='name')

    @property
    def main_field(self):
        return self.name


class SubjectGroupModel(BasicModel):
    title = 'Учебный план'
    table_name = 'subject_group'

    def __init__(self):
        super().__init__()
        self.subject = ForeignKeyField(title='Предмета', col_name='subject_id', target_model=SubjectsModel, target_fields=(('name', 'Название предмета'),))
        self.groups = ForeignKeyField(title='Группа', col_name='group_id', target_model=GroupsModel, target_fields=(('name', 'Название группы'),))


class SubjectTeacherModel(BasicModel):
    title = 'Нагрузка учителя'
    table_name = 'subject_teacher'

    def __init__(self):
        super().__init__()
        self.subject = ForeignKeyField(title='Предмет', col_name='subject_id', target_model=SubjectsModel, target_fields=(('name', 'Название предмета'),))
        self.teacher = ForeignKeyField(title='Учитель', col_name='teacher_id', target_model=TeachersModel, target_fields=(('name', 'ФИО Преподавателя'),))


class TeachersModel(BasicModel):
    title = 'Учителя'
    table_name = 'teachers'

    def __init__(self):
        super().__init__()
        self.name = StringField('ФИО', col_name='name')

    @property
    def main_field(self):
        return self.name


class WeekdaysModel(BasicModel):
    title = 'Дни недели'
    table_name = 'weekdays'

    def __init__(self):
        super().__init__()
        self.name = StringField('Название', col_name='name')
        self.order_number = IntegerField('Порядковый номер', col_name='order_number')

    @property
    def main_field(self):
        return self.name


class SchedItemsModel(BasicModel):
    title = 'Расписание'
    table_name = 'sched_items'

    def __init__(self):
        super().__init__()
        self.lesson = ForeignKeyField(title='Пара', col_name='lesson_id', target_model=LessonsModel, target_fields=(('name', 'Пара'),))
        self.subject = ForeignKeyField(title='Предмет', col_name='subject_id', target_model=SubjectsModel, target_fields=(('name', 'Предмет'),))
        self.audience = ForeignKeyField(title='Аудитория', col_name='audience_id', target_model=AudienceModel, target_fields=(('name', 'Аудитория'),))
        self.group = ForeignKeyField(title='Группа', col_name='group_id', target_model=GroupsModel, target_fields=(('name', 'Группа'),))
        self.teacher = ForeignKeyField(title='Учитель', col_name='teacher_id', target_model=TeachersModel, target_fields=(('name', 'ФИО Преподавателя'),))
        self.type = ForeignKeyField(title='Типы пары', col_name='type_id', target_model=LessonTypesModel, target_fields=(('name', 'Тип'),))
        self.weekday = ForeignKeyField(title='День недели', col_name='weekday_id', target_model=WeekdaysModel, target_fields=(('name', 'День недели'),))


class LogStatusModel(BasicModel):
    title = 'Статус записи'
    table_name = 'log_status'

    def __init__(self):
        super().__init__()
        self.name = StringField('Статус', col_name='name')

    @property
    def main_field(self):
        return self.name


class LogModel(BasicModel):
    title = 'Логи'
    table_name = 'log'

    def __init__(self):
        super().__init__()
        self.status = ForeignKeyField(title='Статус', col_name='status', target_model=LogStatusModel, target_fields=(('name', 'Статус'),))
        self.logged_table_name = StringField(col_name='table_name', title='Таблица')
        self.logged_table_pk = IntegerField(col_name='table_pk', title='Ключ')
        # TODO: fix creation
        self.datetime = TimestampField(col_name='change_time', title='Время')

    def get_changes(self, date_start, pks, table_name):
        cur = get_cursor()
        sql = SQLLogSelect(target_table=self)
        sql = self.select_all_fields(sql)#there is no pk!! fix in future
        sql.add_custom_condition(CustomCondition(field_name=self.datetime.col_name, compare_operator='>', val=date_start))
        sql.add_custom_condition(CustomCondition(field_name=self.datetime.col_name, compare_operator='<', val=datetime.now()))
        sql.add_custom_condition(CustomCondition(field_name=self.logged_table_name.col_name,
                                                 compare_operator='=', val=table_name))
        group_pk = GroupCondition('AND')
        for pk in pks:
            group_pk.add_condition(CustomCondition(field_name=self.logged_table_pk.col_name,
                                                     val=pk,
                                                     compare_operator='=',
                                                     logic_operator='OR'))

        sql.add_group_condition(group_pk)
        sql.execute(cur)
        return cur.fetchallmap()


all_models = (
        AudienceModel,
        GroupsModel,
        LessonsModel,
        LessonTypesModel,
        SchedItemsModel,
        SubjectsModel,
        SubjectGroupModel,
        SubjectTeacherModel,
        TeachersModel,
        WeekdaysModel,
        LogStatusModel,
        LogModel
)
