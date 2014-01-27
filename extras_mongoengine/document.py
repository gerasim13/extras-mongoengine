from mongoengine.base import TopLevelDocumentMetaclass
from mongoengine.queryset import QuerySet
from mongoengine.document import Document


class SoftDeleteQuerySet(QuerySet):

    def __init__(self, *args, **kwargs):
        super(SoftDeleteQuerySet, self).__init__(*args, **kwargs)
        assert 'soft_delete' in self._document._meta
        assert type(self._document._meta['soft_delete']) is dict

        soft_delete = self._document._meta['soft_delete']
        for key in soft_delete:
            if key in kwargs:
                continue
            if type(soft_delete[key]) is bool:
                self._initial_query[key] = not soft_delete[key]
            else:
                self._initial_query[key] = {'$ne': soft_delete[key]}

    def __call__(self, q_obj=None, class_check=True, slave_okay=False,
            read_preference=None, **query):
        for key in set(query).intersection(self._document._meta['soft_delete']):
            del self._initial_query[key]
        return super(SoftDeleteQuerySet, self).__call__(q_obj=None,
                class_check=True, slave_okay=False, read_preference=None,
                **query)

    def including_soft_deleted(self):
        for key in self._document._meta['soft_delete']:
            del self._initial_query[key]
        return self.clone()


class SoftDeleteDocument(Document):
    my_metaclass = TopLevelDocumentMetaclass
    __metaclass__ = TopLevelDocumentMetaclass

    meta = {'queryset_class': SoftDeleteQuerySet}

    @property
    def _qs(self):  #FIXME
        """
        Returns the queryset to use for updating / reloading / deletions
        """
        if not hasattr(self, '__objects'):
            queryset_class = self._meta.get('queryset_class', QuerySet)
            self.__objects = queryset_class(self, self._get_collection())
        return self.__objects

    def soft_delete(self):
        soft_delete = self._meta.get('soft_delete')
        cls_name = self.__class__.__name__
        assert soft_delete, "%s's meata doesn't exist" % cls_name
        assert type(soft_delete) is dict, \
                "%s's soft_delete must be a dictionary" % cls_name
        for key in soft_delete:
            assert key in self._fields, \
                    "%s's meta has no field %s" % (cls_name, key)
            setattr(self, key, soft_delete[key])
        self.save()
