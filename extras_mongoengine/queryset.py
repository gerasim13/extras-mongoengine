from mongoengine.queryset import QuerySet


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
