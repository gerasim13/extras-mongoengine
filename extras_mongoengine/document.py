from mongoengine.base import TopLevelDocumentMetaclass
from mongoengine.queryset import QuerySet, OperationError
from mongoengine.document import Document


class SoftDeleteQuerySet(QuerySet):

    def __init__(self, *args, **kwargs):
        super(SoftDeleteQuerySet, self).__init__(*args, **kwargs)
        soft_delete = self._document._meta.get('soft_delete', None)
        assert type(soft_delete) is dict

        for key in soft_delete:
            if key in kwargs:
                continue
            if type(soft_delete[key]) is bool:
                self._initial_query[key] = not soft_delete[key]
            else:
                self._initial_query[key] = {'$ne': soft_delete[key]}

    def __call__(self, q_obj=None, class_check=True, slave_okay=False,
            read_preference=None, **query):
        """A simple wrapper around ~mongoengine.queryset.QuerySet.__call__ that
        allows query parameters to override those written in the initial query.
        """
        for key in set(query).intersection(self._document._meta['soft_delete']):
            del self._initial_query[key]
        return super(SoftDeleteQuerySet, self).__call__(q_obj=None,
                class_check=True, slave_okay=False, read_preference=None,
                **query)

    @property
    def including_soft_deleted(self):
        """Will clean the queryset from soft_delete notions."""
        for key in set(self._initial_query)\
                .intersection(self._document._meta['soft_delete']):
            del self._initial_query[key]
        return self.clone()


class SoftDeleteDocument(Document):
    my_metaclass = TopLevelDocumentMetaclass
    __metaclass__ = TopLevelDocumentMetaclass

    meta = {'queryset_class': SoftDeleteQuerySet}

    @property
    def _qs(self):  #FIXME should be present in mongoengine ?
        """Returns the queryset to use for updating / reloading / deletions."""
        if not hasattr(self, '__objects'):
            queryset_class = self._meta.get('queryset_class', QuerySet)
            self.__objects = queryset_class(self, self._get_collection())
        return self.__objects

    def soft_delete(self):
        """Won't delete the document as much as marking it as deleted according
        to parameters present in meta.
        """
        for key in self._meta.get('soft_delete', {}):
            setattr(self, key, self._meta['soft_delete'][key])
        self.save()

    @property
    def is_soft_deleted(self):
        """Return true if the field of the document are set according to the
        soft deleted state as defined in the metas.
        """
        for key in self._meta.get('soft_delete', {}):
            if not self._meta['soft_delete'][key] == getattr(self, key):
                return False
        return True


    def update(self, **kwargs):
        """The ~mongoengine.Document.update method had to be overriden
        so it's not soft_delete aware and will update document
        no matter the "soft delete" state.
        """
        if not self.pk:
            if kwargs.get('upsert', False):
                query = self.to_mongo()
                if "_cls" in query:
                    del(query["_cls"])
                return self._qs.including_soft_deleted\
                        .filter(**query).update_one(**kwargs)
            else:
                raise OperationError('attempt to update a document not yet saved')
        return self._qs.including_soft_deleted\
                .filter(**self._object_key).update_one(**kwargs)
