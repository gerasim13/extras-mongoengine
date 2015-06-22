# -*- coding: utf-8 -*-
import weakref
from mongoengine.common import _import_class

class BaseSet(set):
    """A special list so we can watch any changes
    """

    _dereferenced = False
    _instance = None
    _name = None

    def __init__(self, list_items, instance, name):
        Document = _import_class('Document')
        EmbeddedDocument = _import_class('EmbeddedDocument')

        if isinstance(instance, (Document, EmbeddedDocument)):
            self._instance = weakref.proxy(instance)
        self._name = name
        super(BaseSet, self).__init__(list_items)

    def add(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseSet, self).add(*args, **kwargs)

    def update(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseSet, self).update(*args, **kwargs)

    def pop(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseSet, self).pop(*args, **kwargs)

    def remove(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseSet, self).remove(*args, **kwargs)

    def clear(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseSet, self).clear(*args, **kwargs)

    def _mark_as_changed(self):
        if hasattr(self._instance, '_mark_as_changed'):
            self._instance._mark_as_changed(self._name)
