class ReadOnlyRouter:
    def db_for_read(self, model, **hints):
        return 'readonly'

    def db_for_write(self, model, **hints):
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        db_set = {'default', 'readonly'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == 'default'
