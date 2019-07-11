#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-graph
# Created by the Natural History Museum in London, UK

import logging

from ckanext.graph.db import ElasticSearchQuery
from ckanext.graph.lib import utils
from ckanext.graph.logic.validators import in_list, is_boolean, is_date_castable

import ckanext.datastore.interfaces as datastore_interfaces
from ckan.plugins import (PluginImplementations, SingletonPlugin, implements, interfaces,
                          toolkit)

not_empty = toolkit.get_validator(u'not_empty')
ignore_empty = toolkit.get_validator(u'ignore_empty')

log = logging.getLogger(__name__)

DATE_INTERVALS = [u'minute', u'hour', u'day', u'month', u'year']

TEMPORAL_FIELD_TYPES = [u'date']


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

    def setup_template_variables(self, context, data_dict):
        '''Setup variables available to templates

        :param context:
        :param data_dict:

        '''

        datastore_fields = utils.get_datastore_field_types()
        self.datastore_field_names = datastore_fields.keys()

        dropdown_options_count = [{
            u'value': field_name,
            u'text': field_name
            } for field_name, field_type in
            datastore_fields.items()]

        dropdown_options_date = [{
            u'value': field_name,
            u'text': field_name
            } for field_name, field_type in
            datastore_fields.items() if
            field_type in TEMPORAL_FIELD_TYPES or 'date' in field_name.lower() or 'time' in
            field_name.lower()]

        vars = {
            u'count_field_options': [None] + sorted(dropdown_options_count,
                                                    key=lambda x: x['text']),
            u'date_field_options': [None] + sorted(dropdown_options_date,
                                                   key=lambda x: x['text']),
            u'date_interval_options': [{
                u'value': interval,
                u'text': interval
                } for interval in DATE_INTERVALS],
            u'defaults': {},
            u'graphs': [],
            u'resource': data_dict[u'resource']
            }

        if data_dict[u'resource_view'].get(u'show_count', None) and data_dict[u'resource_view'].get(
            u'count_field', None):

            count_field = data_dict[u'resource_view'].get(u'count_field')

            count_query = ElasticSearchQuery(count_field=count_field)

            records = count_query.run()

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
                    key, count = record
                    count_dict[u'data'].append([i, count])
                    count_dict[u'options'][u'xaxis'][u'ticks'].append([i, key.title()])

                vars[u'graphs'].append(count_dict)

        # Do we want a date statistics graph
        if data_dict[u'resource_view'].get(u'show_date', False) and data_dict[
            u'resource_view'].get(u'date_field', None) is not None:

            date_interval = data_dict[u'resource_view'].get(u'date_interval')
            date_field = data_dict[u'resource_view'].get(u'date_field')

            date_query = ElasticSearchQuery(date_field=date_field, date_interval=date_interval)

            records = date_query.run()

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
                    timestamp, count = record
                    total += count
                    total_dict[u'data'].append([timestamp, total])
                    count_dict[u'data'].append([timestamp, count])

                vars[u'graphs'].append(total_dict)
                vars[u'graphs'].append(count_dict)

        return vars