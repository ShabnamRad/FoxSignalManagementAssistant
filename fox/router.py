class StockRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'bourse_refs':
            return 'bourse_refs'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'bourse_refs':
            return 'bourse_refs'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'bourse_refs' or obj2._meta.app_label == 'bourse_refs':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'bourse_refs':
            return db == 'bourse_main'
        return None
