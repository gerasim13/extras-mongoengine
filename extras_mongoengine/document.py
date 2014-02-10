from mongoengine.base import TopLevelDocumentMetaclass
from mongoengine.queryset import QuerySet, OperationError
from mongoengine.document import Document

from extras_mongoengine import signals
from extras_mongoengine.queryset import SoftDeleteQuerySet


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
        signals.pre_soft_delete.send(self.__class__, document=self)
        for key in self._meta.get('soft_delete', {}):
            setattr(self, key, self._meta['soft_delete'][key])
        self.save()
        signals.post_soft_delete.send(self.__class__, document=self)

    def soft_undelete(self):
        """Will undelete the document
        """
        signals.pre_soft_undelete.send(self.__class__, document=self)
        for key in self._meta.get('soft_delete', {}):
            # FIXME: this won't work with non-boolean attributes
            undelete_value = not self._meta['soft_delete'][key]
            setattr(self, key, undelete_value)
        self.save()
        signals.post_soft_undelete.send(self.__class__, document=self)

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
