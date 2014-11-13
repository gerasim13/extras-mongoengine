from mongoengine.queryset import QuerySet


class SoftDeleteQuerySet(QuerySet):

    def __init__(self, *args, **kwargs):
        super(SoftDeleteQuerySet, self).__init__(*args, **kwargs)

        not_soft_deleted_conditions = self._not_soft_deleted_cond(**kwargs)
        self._initial_query.update(not_soft_deleted_conditions)

    def __to_mongo(self, key, val):
        return self._document._fields[key].to_mongo(val)

    def _not_soft_deleted_cond(self, **kwargs):
        """Query conditions for documents that are not soft deleted
        """
        cond = {}
        for key, val in self._document._meta.get('soft_delete', {}).items():
            if key in kwargs:  # not overriding kwargs
                continue
            if type(val) is bool:
                cond[key] = not val
            else:
                cond[key] = {'$ne': self.__to_mongo(key, val)}
        return cond

    def __call__(self, q_obj=None, class_check=True, slave_okay=False,
            read_preference=None, **query):
        """A simple wrapper around ~mongoengine.queryset.QuerySet.__call__ that
        allows query parameters to override those written in the initial query.
        """
        soft_delete_attrs = self._document._meta.get('soft_delete', {})
        for key in set(query).intersection(soft_delete_attrs):
            del self._initial_query[key]
        return super(SoftDeleteQuerySet, self).__call__(q_obj=q_obj,
                class_check=class_check, slave_okay=slave_okay,
                read_preference=read_preference, **query)

    @property
    def including_soft_deleted(self):
        """Will clean the queryset from soft_delete notions."""
        soft_delete_attrs = self._document._meta.get('soft_delete', {})
        for key in set(self._initial_query).intersection(soft_delete_attrs):
            del self._initial_query[key]
        return self.clone()

    @property
    def soft_deleted(self):
        soft_delete_attrs = self._document._meta.get('soft_delete', {})
        for field, sd_value in soft_delete_attrs.items():
            self._initial_query[field] = self.__to_mongo(field, sd_value)
        return self.clone()
