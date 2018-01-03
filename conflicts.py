import conditions


class BaseConflict:
    def full_recalculate(self):
        pass


class AudienceOverlap(BaseConflict):
    def __init__(self):
        super().__init__()


all_conflicts = (
    AudienceOverlap(),
)

def recalculate_all(cur, sched_conflicts_model, conflicts_model, sched_model):
    cur.execute('''RECREATE TABLE {table_name}
                (
                    ID Integer NOT NULL,
                    CONFLICT_ID Integer NOT NULL,
                    SCHED_ID Integer NOT NULL,
                    PRIMARY KEY (ID)
                )'''.format(table_name=sched_conflicts_model.table_name))

    cur.execute('''RECREATE TABLE {table_name}
                (
                    ID Integer NOT NULL,
                    NAME Varchar(255) NOT NULL,
                    PRIMARY KEY (ID)
                );
                '''.format(table_name=conflicts_model.table_name))

    cur.execute('''ALTER TABLE {sched_conflicts_table_name} ADD
                    FOREIGN KEY ({conflict_id_col_name}) REFERENCES {conflicts_table_name} (ID)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE;'''.format(sched_conflicts_table_name=sched_conflicts_model.table_name,
                                                 conflict_id_col_name=sched_conflicts_model.conflict.col_name,
                                                 conflicts_table_name=conflicts_model.table_name))

    cur.execute('''ALTER TABLE {sched_conflicts_table_name} ADD
                        FOREIGN KEY ({conflict_id_col_name}) REFERENCES {conflicts_table_name} (ID)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE;'''.format(sched_conflicts_table_name=sched_conflicts_model.table_name,
                                                     conflict_id_col_name=sched_conflicts_model.sched_item.col_name,
                                                     conflicts_table_name=sched_model.table_name))

    conflicts = ((1, 'Совпадение аудиторий'),
                 (2, 'Совпадение преподавателей'))

    cur.transaction.commit()
    cur.executemany('INSERT INTO {tablename} values (?, ?)'.format(tablename=conflicts_model.table_name), conflicts)

    # TODO: drop conflict database
    for conflict in all_conflicts:
        conflict.full_recalculate()