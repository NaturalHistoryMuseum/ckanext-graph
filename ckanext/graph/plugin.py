#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-graph
# Created by the Natural History Museum in London, UK

import datetime
import logging
import urllib

import dateutil.parser
from ckanext.graph.db import run_stats_query
from ckanext.graph.logic.validators import in_list, is_boolean, is_date_castable

import ckanext.datastore.interfaces as datastore_interfaces
from ckan.plugins import (PluginImplementations, SingletonPlugin, implements, interfaces,
                          toolkit)

not_empty = toolkit.get_validator(u'not_empty')
ignore_empty = toolkit.get_validator(u'ignore_empty')

log = logging.getLogger(__name__)

DATE_INTERVALS = [u'minute', u'hour', u'day', u'month', u'year']

TEMPORAL_FIELD_TYPES = [u'text', u'timestamp', u'date', u'citext']


class GraphPlugin(SingletonPlugin):
    '''Graph plugin'''
    implements(interfaces.IConfigurer)
    implements(interfaces.IResourceView, inherit=True)
    implements(datastore_interfaces.IDatastore, inherit=True)
    datastore_field_names = []

    ## IConfigurer
    def update_config(self, config):
        '''Add our template directories to the list of available templates

        :param config: 

        '''
        toolkit.add_template_directory(config, u'theme/templates')
        toolkit.add_public_directory(config, u'theme/public')
        toolkit.add_resource(u'theme/public', u'ckanext-graph')

    ## IResourceView
    def info(self):
        ''' '''
        return {
            u'name': u'graph',
            u'title': u'Graph',
            u'schema': {
                u'show_date': [is_boolean],
                u'date_field': [ignore_empty, is_date_castable,
                                in_list(self.datastore_field_names)],
                u'date_interval': [not_empty, in_list(DATE_INTERVALS)],
                u'show_count': [is_boolean],
                u'count_field': [ignore_empty, in_list(self.datastore_field_names)],
                u'count_label': [],
                },
            u'icon': u'bar-chart',
            u'iframed': False,
            u'filterable': True,
            u'preview_enabled': False,
            u'full_page_edit': False
            }

    # IDatastore
    def datastore_search(self, context, data_dict, all_field_ids, query_dict):
        '''

        :param context: 
        :param data_dict: 
        :param all_field_ids: 
        :param query_dict: 

        '''
        return query_dict

    def datastore_validate(self, context, data_dict, all_field_ids):
        '''

        :param context: 
        :param data_dict: 
        :param all_field_ids: 

        '''
        return data_dict

    def view_template(self, context, data_dict):
        '''

        :param context: 
        :param data_dict: 

        '''
        return u'graph/view.html'

    def form_template(self, context, data_dict):
        '''

        :param context: 
        :param data_dict: 

        '''
        return u'graph/form.html'

    def can_view(self, data_dict):
        '''Specify which resources can be viewed by this plugin

        :param data_dict: 

        '''
        # Check that we have a datastore for this resource
        if data_dict[u'resource'].get(u'datastore_active'):
            return True
        return False

    def _query(self, context, select, resource_id, group_by=u''):
        '''

        :param context: 
        :param select: 
        :param resource_id: 
        :param group_by:  (Default value = u'')

        '''

        # Build a data dict, ready to pass through to datastore interfaces
        data_dict = {
            u'connection_url': toolkit.config[u'ckan.datastore.write_url'],
            u'resource_id': resource_id,
            u'filters': self._get_request_filters(),
            u'q': urllib.unquote(toolkit.request.params.get(u'q', u''))
            }

        field_types = self._get_datastore_fields(resource_id)

        (ts_query, where_clause, values) = self._get_request_where_clause(data_dict,
                                                                          field_types)

        # Prepare and run our query
        return run_stats_query(select, resource_id, ts_query, where_clause, group_by,
                               values)

    def _get_request_where_clause(self, data_dict, field_types):
        '''Return the where clause that applies to a query matching the given request

        :param data_dict: A dictionary representing a datastore API request
        :param field_types: A dictionary of field name to field type. Must
                            include all the fields that may be used in the
                            query
        :returns: Tuple defining (
                    extra from statement for full text queries,
                    where clause,
                    list of replacement values
                )

        '''
        query_dict = {
            u'select': [],
            u'sort': [],
            u'where': []
            }

        for plugin in PluginImplementations(interfaces.IDatastore):
            query_dict = plugin.datastore_search(
                {}, data_dict, field_types, query_dict
                )

        clauses = []
        values = []

        for clause_and_values in query_dict[u'where']:
            clauses.append(u'(' + clause_and_values[0] + u')')
            values += clause_and_values[1:]

        where_clause = u' AND '.join(clauses)
        if where_clause:
            where_clause = u'WHERE ' + where_clause

        if u'ts_query' in query_dict and query_dict[u'ts_query']:
            ts_query = query_dict[u'ts_query']
        else:
            ts_query = u''

        return ts_query, where_clause, values

    def _get_request_filters(self):
        ''' '''
        filters = {}
        for f in urllib.unquote(toolkit.request.params.get(u'filters', u'')).split(u'|'):
            if f:
                (k, v) = f.split(u':', 1)
                if k not in filters:
                    filters[k] = []
                filters[k].append(v)
        return filters

    def setup_template_variables(self, context, data_dict):
        '''Setup variables available to templates

        :param context: 
        :param data_dict: 

        '''

        datastore_fields = self._get_datastore_fields(data_dict[u'resource'][u'id'])

        self.datastore_field_names = datastore_fields.keys()

        vars = {
            u'count_field_options': [None] + [{
                u'value': field_name,
                u'text': field_name
                } for field_name, field_type in
                datastore_fields.items()],
            u'date_field_options': [None] + [{
                u'value': field_name,
                u'text': field_name
                } for field_name, field_type in
                datastore_fields.items() if
                field_type in TEMPORAL_FIELD_TYPES],
            u'date_interval_options': [{
                u'value': interval,
                u'text': interval
                } for interval in DATE_INTERVALS],
            u'defaults': {},
            u'graphs': [],
            u'resource': data_dict[u'resource']
            }

        if data_dict[u'resource_view'].get(u'show_count', None) and data_dict[
            u'resource_view'].get(u'count_field', None):

            count_field = data_dict[u'resource_view'].get(u'count_field')

            select = u'"{count_field}" as fld, count (*) as count'.format(
                count_field=count_field
                )

            records = self._query(context, select, data_dict[u'resource'][u'id'],
                                  group_by=u'GROUP BY "%s" ORDER BY count DESC LIMIT '
                                           u'25' % count_field)

            if records:

                count_dict = {
                    u'title': data_dict[u'resource_view'].get(u'count_label',
                                                              None) or count_field,
                    u'data': [],
                    u'options': {
                        u'bars': {
                            u'show': True,
                            u'barWidth': 0.6,
                            u'align': u'center'
                            },
                        u'xaxis': {
                            u'ticks': [],
                            u'rotateTicks': 60,
                            }
                        }
                    }

                for i, record in enumerate(records):
                    fld = u'Empty' if record[u'fld'] is None else record[u'fld']
                    count_dict[u'data'].append([i, record[u'count']])
                    count_dict[u'options'][u'xaxis'][u'ticks'].append([i, fld])

                vars[u'graphs'].append(count_dict)

        # Do we want a date statistics graph
        if data_dict[u'resource_view'].get(u'show_date', None) and data_dict[
            u'resource_view'].get(u'date_field', None):

            date_interval = data_dict[u'resource_view'].get(u'date_interval')

            select = u'date_trunc(\'{date_interval}\', "{date_field}"::timestamp) AS ' \
                     u'date, COUNT(*) AS count'.format(
                date_interval=date_interval,
                date_field=data_dict[u'resource_view'].get(u'date_field')
                )

            records = self._query(context, select, data_dict[u'resource'][u'id'],
                                  group_by=u'GROUP BY 1 ORDER BY 1')

            if records:

                default_options = {
                    u'grid': {
                        u'hoverable': True,
                        u'clickable': True
                        },
                    u'xaxis': {
                        u'mode': u'time'
                        },
                    u'yaxis': {
                        u'tickDecimals': 0
                        }
                    }

                total_dict = {
                    u'title': u'Total records',
                    u'data': [],
                    u'options': {
                        u'series': {
                            u'lines': {
                                u'show': True
                                },
                            u'points': {
                                u'show': True
                                }
                            },
                        u'_date_interval': date_interval
                        },

                    }

                count_dict = {
                    u'title': u'Per %s' % date_interval,
                    u'data': [],
                    u'options': {
                        u'series': {
                            u'bars': {
                                u'show': True,
                                u'barWidth': 0.6,
                                u'align': u'center'
                                }
                            }
                        }
                    }

                total_dict[u'options'].update(default_options)
                count_dict[u'options'].update(default_options)

                total = 0

                for record in records:
                    # Convert to string, and then parse as dates
                    # This works for all date and string fields
                    date = dateutil.parser.parse(str(record[u'date']))
                    count = int(record[u'count'])
                    label = int(
                        (date - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)
                    total += count
                    total_dict[u'data'].append([label, total])
                    count_dict[u'data'].append([label, count])

                vars[u'graphs'].append(total_dict)
                vars[u'graphs'].append(count_dict)

        return vars

    def _get_datastore_fields(self, resource_id):
        '''

        :param resource_id: 

        '''

        data = {
            u'resource_id': resource_id,
            u'limit': 0
            }
        fields = toolkit.get_action(u'datastore_search')({}, data)[u'fields']

        field_types = dict([(f[u'id'], f[u'type']) for f in fields])
        field_types[u'_id'] = u'int'

        return field_types


def _get_records_from_datastore(resource, limit, offset):
    '''

    :param resource: 
    :param limit: 
    :param offset: 

    '''
    data = {
        u'resource_id': resource[u'id']
        }
    if limit:
        data[u'limit'] = limit
    if offset:
        data[u'offset'] = offset
    records = toolkit.get_action(u'datastore_search')({}, data)[u'records']
    return records
