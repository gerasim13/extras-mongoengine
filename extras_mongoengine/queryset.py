from mongoengine.queryset import QuerySet


class SoftDeleteQuerySet(QuerySet):

    def __init__(self, *args, **kwargs):
        super(SoftDeleteQuerySet, self).__init__(*args, **kwargs)

        not_soft_deleted_conditions = self._not_soft_deleted_conditions(**kwargs)
        self._initial_query.update(not_soft_deleted_conditions)

    def _not_soft_deleted_conditions(self, **kwargs):
        """Query conditions for documents that are not soft deleted
        """
        conditions = {}
        soft_delete = self._document._meta.get('soft_delete', {})

        for key in soft_delete:
            if key in kwargs:  # not overriding kwargs
                continue
            if type(soft_delete[key]) is bool:
                conditions[key] = not soft_delete[key]
            else:
                conditions[key] = {'$ne': soft_delete[key]}
        return conditions

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
        for key in soft_delete_attrs:
            self._initial_query[key] = soft_delete_attrs[key]
        return self.clone()
