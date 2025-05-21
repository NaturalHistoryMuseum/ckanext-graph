#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-graph
# Created by the Natural History Museum in London, UK

from abc import abstractmethod, abstractproperty

from ckan.plugins import toolkit

from ckanext.graph.lib import utils


class Query(object):
    """
    A base class for retrieving stats from the datastore.

    Subclass to implement different backend retrieval methods.
    """

    def __init__(self, date_field=None, date_interval=None, count_field=None):
        """
        Construct a new Query object. Use EITHER date args OR count args. Using both
        will fail.

        :param date_field: the name of the field to use for dates
        :param date_interval: the length of time between date groupings, e.g. day, month
        :param count_field: the name of the field to use for categories
        """
        if date_field is not None:
            assert count_field is None
        self.resource_id = toolkit.c.resource['id']
        self.filters = utils.get_request_filters()
        self.q = utils.get_request_query()
        self.date_field = date_field
        self.date_interval = date_interval or 'day'
        self.count_field = count_field
        self._is_date_query = date_field is not None

    @property
    def query(self):
        """
        Returns the appropriate query text to send to the datastore backend.

        :returns: the date query or count query
        """
        if self._is_date_query:
            return self._date_query
        else:
            return self._count_query

    @abstractproperty
    def _date_query(self):
        """
        A query for retrieving results grouped by the date in date_field (in
        chronological order, where the interval is date_interval).

        :returns: a query ready to submit to the backend
        """
        return ''

    @abstractproperty
    def _count_query(self):
        """
        A query for retrieving results grouped by the categories in count_field.

        :returns: a query ready to submit to the backend
        """
        return ''

    @abstractmethod
    def run(self):
        """
        Submits the query to the backend and processes the results into the format
        [(key, count)].

        :returns: a list of (key,count) tuples
        """
        pass

    @classmethod
    def new(cls, *args, **kwargs):
        backend_type = toolkit.config.get('ckanext.graph.backend')
        queries = {'elasticsearch': ElasticSearchQuery, 'sql': SqlQuery}
        query_class = queries.get(backend_type, ElasticSearchQuery)
        return query_class(*args, **kwargs)


class ElasticSearchQuery(Query):
    def __init__(self, *args, **kwargs):
        super(ElasticSearchQuery, self).__init__(*args, **kwargs)
        self._bucket_name = 'query_buckets'
        self._aggregated_name = 'agg_buckets'

    def _nest(self, *query_stack):
        """
        Helper method for nesting multiple dicts inside each other (nested stacks can
        get quite deep in elastic search queries).

        :param query_stack: the items to nest, in descending order (i.e. the first item
            will be the outermost key)
        :returns: a dict of nested items
        """
        nested = query_stack[-1]
        for i in query_stack[-2::-1]:
            nested = {i: nested}
        return nested

    @property
    def _filter_stack(self):
        """
        Create the subquery for filtering records (mostly from URL parameters, but date
        graphs also require that the date field is not null).

        :returns: a dict of filter items
        """
        if self._is_date_query:
            filters = [self._nest('exists', 'field', f'data.{self.date_field}')]
        else:
            filters = []

        if self.q is not None:
            filters.append(self._nest('query_string', 'query', self.q))

        def _make_filter_term(filter_field, filter_value):
            if isinstance(filter_value, list):
                if len(filter_value) == 1:
                    return _make_filter_term(filter_field, filter_value[0])
                else:
                    terms = [
                        _make_filter_term(filter_field, sub_value)
                        for sub_value in filter_value
                    ]
                    return self._nest('bool', 'should', terms)
            else:
                filter_dict = {f'data.{filter_field}': filter_value}
                return {'term': filter_dict}

        for f, v in self.filters.items():
            filters.append(_make_filter_term(f, v))

        filter_stack = self._nest('filter', 'bool', 'must', filters)

        return filter_stack

    @property
    def _date_query(self):
        field_type = utils.get_datastore_field_types()[self.date_field]

        if field_type == 'date':
            histogram_options = {'field': f'data.{self.date_field}._d'}
        else:
            script = f"""try {{
              def parser = new SimpleDateFormat(\'yyyy-MM-dd\');
              def dt = parser.parse(doc[\'data.{self.date_field}\'].value);
              return dt.getTime();
             }} catch (Exception e) {{
              return false;
             }}"""
            histogram_options = {'script': script}

        histogram_options['calendar_interval'] = self.date_interval

        select_stack = self._nest(
            'aggs', self._bucket_name, 'date_histogram', histogram_options
        )

        select_stack.update(self._filter_stack)

        query_stack = self._nest('aggs', self._aggregated_name, select_stack)

        return query_stack

    @property
    def _count_query(self):
        agg_options = {
            'field': f'data.{self.count_field}',
            'missing': toolkit._('Empty'),
        }

        query_stack = self._nest('aggs', self._bucket_name, 'terms', agg_options)

        if len(self.filters) > 0 or self.q is not None:
            query_stack.update(self._filter_stack)
            query_stack = self._nest('aggs', self._aggregated_name, query_stack)

        return query_stack

    def run(self):
        # the vds_multi_direct action is admin only to prevent misuse, but we know what
        # we're doing, so skip the auth check
        context = {'ignore_auth': True}
        data_dict = {'resource_ids': [self.resource_id], 'search': self.query}
        results = toolkit.get_action('vds_multi_direct')(context, data_dict)
        aggs = results['aggregations']
        extra_nesting = (
            self._is_date_query or len(self.filters) > 0 or self.q is not None
        )
        buckets = (aggs[self._aggregated_name] if extra_nesting else aggs)[
            self._bucket_name
        ]['buckets']
        records = [(b['key'], b.get('doc_count', 0)) for b in buckets]
        return records


class SqlQuery(Query):
    @property
    def _date_query(self):
        raise NotImplementedError()

    @property
    def _count_query(self):
        raise NotImplementedError()

    def run(self):
        raise NotImplementedError()
