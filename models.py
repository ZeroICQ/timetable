import flask
import fdb
from fields import BaseField, IntegerField, StringField, PKField, ForeignKeyField, TimestampField
from sqlbuilder import SQLSelect, SQLCountAll, SQLBasicUpdate, SQLBasicDelete, SQLBasicInsert, SQLLogSelect
from math import ceil
from conditions import BetweenCondition, BasicCondition, InCondition
import conflicts


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

    actions = {'deleted': 1,
               'modified': 2}

    def __init__(self):
        super().__init__()
        self.pagination = None
        self.pk = PKField()
        self._fields = None
        self._fields_short_resolved = None
        self._fields_own = None
        self._fields_main = None
        self._fields_no_pk = None
        self._fields_short_resolved_no_pk = None
        self._fields_fks = None

    def _after_init_(self):
        self.resolve_foreign_keys()

    def resolve_foreign_keys(self):
        for field in self.__dict__.values():
            if isinstance(field, BaseField):
                field.table_name = self.table_name
                # possible memory leakage
                if not isinstance(field, ForeignKeyField):
                    field.target_model = self

    def get_field_by_col_name(self, col_name):
        for field in self.fields:
            if field.col_name.lower() == col_name or field.qualified_col_name == col_name:
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
    def fields_fks(self):
        if self._fields_fks is None:
            self._fields_fks = [field for field in self.fields if isinstance(field, ForeignKeyField)]
        return self._fields_fks

    @property
    def fields_no_pk(self):
        if self._fields_no_pk is None:
            self._fields_no_pk = [field for field in self.fields if not isinstance(field, PKField)]
        return self._fields_no_pk

    @property
    def fields_short_resolved(self):
        if self._fields_short_resolved is None:
            self._fields_short_resolved = [self.pk] + self.fields_short_resolved_no_pk
        return self._fields_short_resolved

    @property
    def fields_short_resolved_no_pk(self):
        if self._fields_short_resolved_no_pk is None:
            self._fields_short_resolved_no_pk = self.fields_own + self.fields_main
        return self._fields_short_resolved_no_pk

    @property
    def fields_own(self):
        if self._fields_own is None:
            self._fields_own = [field for field in self.fields if not (isinstance(field, PKField) or isinstance(field, ForeignKeyField))]
        return self._fields_own

    # TODO: optimize
    @property
    def fields_resolved(self):
        return self.fields_short_resolved + self.fields_fks

    @property
    def fields_main(self):
        if self._fields_main is None:
            self._fields_main = [field.target_model.main_field for field in self.fields if isinstance(field, ForeignKeyField)]
        return self._fields_main

    @staticmethod
    def pack_values(fields, values):
        # tuple - one elem. List of tuple - many elements
        if isinstance(values, tuple):
            return {field.qualified_col_name: values[idx] for idx, field in enumerate(fields)}
        elif isinstance(values, list):
            return [{field.qualified_col_name: value[idx] for idx, field in enumerate(fields)} for value in values]
        elif values is None:
            return None
        else:
            raise TypeError

    def get_pages(self, fields=None, conditions=None, pagination=None):
        cur = get_cursor()
        sql = SQLCountAll(self)
        sql.add_conditions(conditions)
        sql.execute(cur)

        rows = cur.fetchone()[0]
        if pagination:
            on_page = pagination[1]
        else:
            on_page = rows

        return ceil(rows/on_page)

    def fetch_all(self, return_fields=None, conditions=None, sort_field=None, sort_order=None, pagination=None, pack=True):
        cur = get_cursor()
        if return_fields is None:
            return_fields = self.fields_short_resolved

        sql = SQLSelect(self, return_fields, pagination)
        sql.add_conditions(conditions)
        sql.sort_order = sort_order
        sql.sort_field_name = sort_field
        sql.execute(cur)

        if not pack:
            return cur.fetchall()

        return self.pack_values(return_fields, cur.fetchall())

    def fetch_by_pk(self, pk_val, fields=None):
        cur = get_cursor()
        if fields is None:
            fields = self.fields_no_pk

        sql = SQLSelect(self, fields)
        sql.add_equal_condition(self.pk.qualified_col_name, pk_val)
        sql.execute(cur)
        return self.pack_values(fields, cur.fetchone())

    def fetch_by_pks(self, pks, fields=None):
        cur = get_cursor()
        if fields is None:
            fields = self.fields_no_pk

        sql = SQLSelect(self, fields)
        sql.add_conditions(InCondition(self.pk.qualified_col_name, pks))
        sql.execute(cur)
        return self.pack_values(fields, cur.fetchall())

    def update(self, return_fields, new_fields, pk_val):
        cur = get_cursor()
        sql = SQLBasicUpdate(self, new_fields, return_fields=self.fields)
        sql.add_equal_condition(self.pk.qualified_col_name, pk_val)
        sql.execute(cur)
        result_fields = cur.fetchone()

        if not all(v is None for v in result_fields):
            self.log_action(cur, 'modified', pk_val)

        cur.transaction.commit()
        return self.pack_values(return_fields, result_fields)

    def delete_by_pk(self, pk_val, return_fields=None):
        cur = get_cursor()
        sql = SQLBasicDelete(self, return_fields=self.fields)
        sql.add_equal_condition(self.pk.qualified_col_name, pk_val)
        sql.execute(cur)
        result_fields = cur.fetchone()

        if not all(v is None for v in result_fields):
            self.log_action(cur, 'deleted', pk_val)

        cur.transaction.commit()
        return self.pack_values(return_fields, result_fields)

    def insert(self, new_fields):
        cur = get_cursor()
        sql = SQLBasicInsert(self, new_fields, [self.pk])
        sql.execute(cur)
        pk = cur.fetchone()[0]
        cur.transaction.commit()
        return pk

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
        self.subject = ForeignKeyField(title='Предмета', col_name='subject_id', target_model_class=SubjectsModel, target_fields=(('name', 'Название предмета'),))
        self.groups = ForeignKeyField(title='Группа', col_name='group_id', target_model_class=GroupsModel, target_fields=(('name', 'Название группы'),))


class SubjectTeacherModel(BasicModel):
    title = 'Нагрузка учителя'
    table_name = 'subject_teacher'

    def __init__(self):
        super().__init__()
        self.subject = ForeignKeyField(title='Предмет', col_name='subject_id', target_model_class=SubjectsModel, target_fields=(('name', 'Название предмета'),))
        self.teacher = ForeignKeyField(title='Учитель', col_name='teacher_id', target_model_class=TeachersModel, target_fields=(('name', 'ФИО Преподавателя'),))


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
        self.lesson = ForeignKeyField(title='Пара', col_name='lesson_id', target_model_class=LessonsModel, target_fields=(('name', 'Пара'),))
        self.subject = ForeignKeyField(title='Предмет', col_name='subject_id', target_model_class=SubjectsModel, target_fields=(('name', 'Предмет'),))
        self.audience = ForeignKeyField(title='Аудитория', col_name='audience_id', target_model_class=AudienceModel, target_fields=(('name', 'Аудитория'),))
        self.group = ForeignKeyField(title='Группа', col_name='group_id', target_model_class=GroupsModel, target_fields=(('name', 'Группа'),))
        self.teacher = ForeignKeyField(title='Учитель', col_name='teacher_id', target_model_class=TeachersModel, target_fields=(('name', 'ФИО Преподавателя'),))
        self.type = ForeignKeyField(title='Типы пары', col_name='type_id', target_model_class=LessonTypesModel, target_fields=(('name', 'Тип'),))
        self.weekday = ForeignKeyField(title='День недели', col_name='weekday_id', target_model_class=WeekdaysModel, target_fields=(('name', 'День недели'),))


class LogStatusModel(BasicModel):
    title = 'Статус записи'
    table_name = 'log_status'

    def __init__(self):
        super().__init__()
        self.name = StringField('Статус', col_name='name')

    @property
    def main_field(self):
        return self.name


class ConflictsModel(BasicModel):
    title = 'Тип конфликта'
    table_name = 'conflicts'

    def __init__(self):
        super().__init__()
        self.name = StringField(col_name='name', title='Название')

    @property
    def main_field(self):
        return self.name


class SchedConflicstModel(BasicModel):
    title = 'Конфликты'
    table_name = 'sched_conflicts'

    def __init__(self):
        super().__init__()
        self.conflict = ForeignKeyField(title='Конфликт', col_name='conflict_id', target_model_class=ConflictsModel, target_fields=(('name', 'Тип'),))
        self.sched_item = ForeignKeyField(title='Элемент', col_name='sched_id', target_model_class=SchedItemsModel, target_fields=(('id','ID элемента'),))

    def full_recalc(self):
        cur = get_cursor()
        conflicts.recalculate_all(cur, self, ConflictsModel(), SchedItemsModel())
        cur.transaction.commit()


class LogModel(BasicModel):
    title = 'Логи'
    table_name = 'log'

    def __init__(self):
        super().__init__()
        self.status = ForeignKeyField(title='Статус', col_name='status', target_model_class=LogStatusModel, target_fields=(('name', 'Статус'),))
        self.logged_table_name = StringField(col_name='table_name', title='Таблица')
        self.logged_table_pk = IntegerField(col_name='table_pk', title='Ключ')
        # TODO: fix creation
        self.datetime = TimestampField(col_name='change_time', title='Время')

    def get_status(self, pk, table_name, past_updated, now_updated):
        cur = get_cursor()
        sql = SQLSelect(self, [self.status.main_field], rows=1)
        sql.add_conditions(BetweenCondition(self.datetime.qualified_col_name, past_updated, now_updated))
        sql.add_equal_condition(self.logged_table_pk.qualified_col_name, pk)
        sql.add_equal_condition(self.logged_table_name.qualified_col_name, table_name)

        sql.sort_field_name = self.datetime.qualified_col_name
        sql.sort_order = 'DESC'
        sql.execute(cur)

        result = cur.fetchone()
        status = result[0] if result else None
        return status

    def get_statuses(self, pks, table_name, past_updated, now_updated):
        cur = get_cursor()
        sql = SQLLogSelect(self, [self.logged_table_pk, self.status.name])
        sql.add_equal_condition(self.logged_table_name.qualified_col_name, table_name)
        sql.add_conditions(BetweenCondition(self.datetime.qualified_col_name, past_updated, now_updated))
        sql.add_conditions(InCondition(self.logged_table_pk.qualified_col_name, pks))

        sql.execute(cur)

        return cur.fetchall()


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
    LogModel,
    ConflictsModel,
    SchedConflicstModel
)
