import copy

from google.appengine.ext import ndb


class UniqueProperty(ndb.StringProperty):
    _unique = None
    _on = None
    _full_name = None

    def __init__(self, *args, **kwargs):
        if 'unique' in kwargs:
            self._unique = kwargs['unique']
            del(kwargs['unique'])

        super(UniqueProperty, self).__init__(*args, **kwargs)


    def make_unique_on(self, model):
        self._on = model
        self._unique = True
        self._full_name = self._name

        parts = self._name.split('.')
        if len(parts) == 2:
            sp = getattr(model, parts[0])
            sp._modelclass = type(model.__name__ + parts[0] + sp._modelclass.__name__, sp._modelclass.__bases__, dict(sp._modelclass.__dict__))

            prop_copy = copy.copy(self)
            prop_copy._name = parts[1]
            sp._modelclass._properties[parts[1]] = prop_copy
            setattr(sp._modelclass, parts[1], prop_copy)


    def _set_value(self, entity, value):
        if not self._unique or not value:
            super(UniqueProperty, self)._set_value(entity, value)
            return

        old_value = self._get_user_value(entity)
        super(UniqueProperty, self)._set_value(entity, value)
        value = self._get_user_value(entity)

        if old_value == value:
            return

        unique_on = self._on or entity
        if (not self._on) and entity and entity.key and entity.key.parent():
            ancestor_query = True
        else:
            ancestor_query = False

        actual_name = self._name
        self._name = getattr(self, '_full_name', None) or self._name
        try:
            if ancestor_query:
                if unique_on.query(self == value, ancestor=entity.key.parent()).get():
                    raise NotUniqueError('The value for ' + (self._verbose_name or self._name) + ' is not unique.')
            else:
                if unique_on.query(self == value).get():
                    raise NotUniqueError('The value for ' + (self._verbose_name or self._name) + ' is not unique.')
        except:
            super(UniqueProperty, self)._set_value(entity, old_value)
            raise
        finally:
            self._name = actual_name


class NotUniqueError(ValueError):
    pass
