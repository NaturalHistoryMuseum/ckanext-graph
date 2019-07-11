#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-graph
# Created by the Natural History Museum in London, UK

from abc import abstractmethod, abstractproperty
from ckanext.graph.lib import utils

from ckan.plugins import toolkit


class Query(object):
    '''
    A base class for retrieving stats from the datastore. Subclass to implement different backend
    retrieval methods.
    '''

    def __init__(self, date_field=None, date_interval=None,
                 count_field=None):
        '''
        Construct a new Query object. Use EITHER date args OR count args. Using both will fail.
        :param date_field: the name of the field to use for dates
        :param date_interval: the length of time between date groupings, e.g. day, month
        :param count_field: the name of the field to use for categories
        '''
        if date_field is not None:
            assert count_field is None
        self.resource_id = toolkit.c.resource[u'id']
        self.filters = utils.get_request_filters()
        self.q = utils.get_request_query()
        self.date_field = date_field
        self.date_interval = date_interval or 'day'
        self.count_field = count_field
        self._is_date_query = date_field is not None

    @property
    def query(self):
        '''
        Returns the appropriate query text to send to the datastore backend.
        :return: the date query or count query
        '''
        if self._is_date_query:
            return self._date_query
        else:
            return self._count_query

    @abstractproperty
    def _date_query(self):
        '''
        A query for retrieving results grouped by the date in date_field (in chronological order,
        where the interval is date_interval).
        :return: a query ready to submit to the backend
        '''
        return ''

    @abstractproperty
    def _count_query(self):
        '''
        A query for retrieving results grouped by the categories in count_field.
        :return: a query ready to submit to the backend
        '''
        return ''

    @abstractmethod
    def run(self):
        '''
        Submits the query to the backend and processes the results into the format [(key, count)].
        :return: a list of (key,count) tuples
        '''
        pass


class ElasticSearchQuery(Query):
    def __init__(self, *args, **kwargs):
        super(ElasticSearchQuery, self).__init__(*args, **kwargs)
        self._bucket_name = u'query_buckets'
        self._aggregated_name = u'agg_buckets'

    def _nest(self, *query_stack):
        '''
        Helper method for nesting multiple dicts inside each other (nested stacks can get quite
        deep in elastic search queries).
        :param query_stack: the items to nest, in descending order (i.e. the first item will be
                            the outermost key)
        :return: a dict of nested items
        '''
        nested = query_stack[-1]
        for i in query_stack[-2::-1]:
            nested = {
                i: nested
                }
        return nested

    @property
    def _filter_stack(self):
        '''
        Create the subquery for filtering records (mostly from URL parameters, but date graphs
        also require that the date field is not null).
        :return: a dict of filter items
        '''
        if self._is_date_query:
            filters = [self._nest(u'exists', u'field', u'data.{0}'.format(self.date_field))]
        else:
            filters = []

        if self.q is not None:
            filters.append(self._nest(u'query_string', u'query', self.q))

        def _make_filter_term(filter_field, filter_value):
            if isinstance(filter_value, list):
                if len(filter_value) == 1:
                    return _make_filter_term(filter_field, filter_value[0])
                else:
                    terms = [_make_filter_term(filter_field, sub_value) for sub_value in
                             filter_value]
                    return self._nest(u'bool', u'should', terms)
            else:
                filter_dict = {
                    u'data.{0}'.format(filter_field): filter_value
                    }
                return {
                    u'term': filter_dict
                    }

        for f, v in self.filters.items():
            filters.append(_make_filter_term(f, v))

        filter_stack = self._nest(u'filter', u'bool', u'must', filters)

        return filter_stack

    @property
    def _date_query(self):
        field_type = utils.get_datastore_field_types()[self.date_field]

        if field_type == u'date':
            histogram_options = {
                u'field': u'data.{0}'.format(self.date_field)
                }
        else:
            script = u'''try {{
              def parser = new SimpleDateFormat(\'yyyy-MM-dd\');
              def dt = parser.parse(doc[\'data.{date_field}\'].value);
              return dt.getTime();
             }} catch (Exception e) {{
              return false;
             }}'''.format(
                date_field=self.date_field
                )
            histogram_options = {
                u'script': script
                }

        histogram_options[u'interval'] = self.date_interval

        select_stack = self._nest(u'aggs', self._bucket_name, u'date_histogram', histogram_options)

        select_stack.update(self._filter_stack)

        query_stack = self._nest(u'aggs', self._aggregated_name, select_stack)

        return query_stack

    @property
    def _count_query(self):
        agg_options = {
            u'field': u'data.{0}'.format(self.count_field),
            u'missing': toolkit._('Empty')
            }

        query_stack = self._nest(u'aggs', self._bucket_name, u'terms', agg_options)

        if len(self.filters) > 0 or self.q is not None:
            query_stack.update(self._filter_stack)
            query_stack = self._nest(u'aggs', self._aggregated_name, query_stack)

        return query_stack

    def run(self):
        data_dict = {
            u'resource_id': self.resource_id,
            u'search': self.query,
            u'raw_result': True
            }
        results = toolkit.get_action('datastore_search_raw')({}, data_dict)
        aggs = results[u'aggregations']
        extra_nesting = self._is_date_query or len(self.filters) > 0
        buckets = (aggs[self._aggregated_name] if extra_nesting else aggs)[self._bucket_name][
            u'buckets']
        records = [(b[u'key'], b.get(u'doc_count', 0)) for b in buckets]
        return records
