#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-graph
# Created by the Natural History Museum in London, UK

import logging

from ckanext.graph.db import Query
from ckanext.graph.lib import utils
from ckanext.graph.logic.validators import in_list, is_boolean, is_date_castable

import ckanext.datastore.interfaces as datastore_interfaces
from ckan.plugins import (SingletonPlugin, implements, interfaces,
                          toolkit)

not_empty = toolkit.get_validator('not_empty')
ignore_empty = toolkit.get_validator('ignore_empty')

log = logging.getLogger(__name__)

DATE_INTERVALS = ['minute', 'hour', 'day', 'month', 'year']

TEMPORAL_FIELD_TYPES = ['date']


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
        toolkit.add_template_directory(config, 'theme/templates')
        toolkit.add_resource('theme/assets', 'ckanext-graph')

    ## IResourceView
    def info(self):
        ''' '''
        return {
            'name': 'graph',
            'title': 'Graph',
            'schema': {
                'show_date': [is_boolean],
                'date_field': [ignore_empty, is_date_castable,
                               in_list(self.datastore_field_names)],
                'date_interval': [not_empty, in_list(DATE_INTERVALS)],
                'show_count': [is_boolean],
                'count_field': [ignore_empty, in_list(self.datastore_field_names)],
                'count_label': [],
            },
            'icon': 'bar-chart',
            'iframed': False,
            'filterable': True,
            'preview_enabled': False,
            'full_page_edit': False
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
        return 'graph/view.html'

    def form_template(self, context, data_dict):
        '''

        :param context:
        :param data_dict:

        '''
        return 'graph/form.html'

    def can_view(self, data_dict):
        '''Specify which resources can be viewed by this plugin

        :param data_dict:

        '''
        # Check that we have a datastore for this resource
        if data_dict['resource'].get('datastore_active'):
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
            'value': field_name,
            'text': field_name
        } for field_name, field_type in
            datastore_fields.items()]

        dropdown_options_date = [{
            'value': field_name,
            'text': field_name
        } for field_name, field_type in
            datastore_fields.items() if
            field_type in TEMPORAL_FIELD_TYPES or 'date' in field_name.lower() or 'time' in
            field_name.lower()]

        vars = {
            'count_field_options': [None] + sorted(dropdown_options_count,
                                                   key=lambda x: x['text']),
            'date_field_options': [None] + sorted(dropdown_options_date,
                                                  key=lambda x: x['text']),
            'date_interval_options': [{
                'value': interval,
                'text': interval
            } for interval in DATE_INTERVALS],
            'defaults': {},
            'graphs': [],
            'resource': data_dict['resource']
        }

        if data_dict['resource_view'].get('show_count', None) and data_dict['resource_view'].get(
            'count_field', None):

            count_field = data_dict['resource_view'].get('count_field')

            count_query = Query.new(count_field=count_field)

            records = count_query.run()

            if records:
                count_dict = {
                    'title': data_dict['resource_view'].get('count_label',
                                                            None) or count_field,
                    'data': [],
                    'options': {
                        'bars': {
                            'show': True,
                            'barWidth': 0.6,
                            'align': 'center'
                        },
                        'xaxis': {
                            'ticks': [],
                            'rotateTicks': 60,
                        }
                    }
                }

                for i, record in enumerate(records):
                    key, count = record
                    count_dict['data'].append([i, count])
                    count_dict['options']['xaxis']['ticks'].append([i, key.title()])

                vars['graphs'].append(count_dict)

        # Do we want a date statistics graph
        if data_dict['resource_view'].get('show_date', False) and data_dict[
            'resource_view'].get('date_field', None) is not None:

            date_interval = data_dict['resource_view'].get('date_interval')
            date_field = data_dict['resource_view'].get('date_field')

            date_query = Query.new(date_field=date_field, date_interval=date_interval)

            records = date_query.run()

            if records:

                default_options = {
                    'grid': {
                        'hoverable': True,
                        'clickable': True
                    },
                    'xaxis': {
                        'mode': 'time'
                    },
                    'yaxis': {
                        'tickDecimals': 0
                    }
                }

                total_dict = {
                    'title': 'Total records',
                    'data': [],
                    'options': {
                        'series': {
                            'lines': {
                                'show': True
                            },
                            'points': {
                                'show': True
                            }
                        },
                        '_date_interval': date_interval
                    },

                }

                count_dict = {
                    'title': 'Per %s' % date_interval,
                    'data': [],
                    'options': {
                        'series': {
                            'bars': {
                                'show': True,
                                'barWidth': 0.6,
                                'align': 'center'
                            }
                        }
                    }
                }

                total_dict['options'].update(default_options)
                count_dict['options'].update(default_options)

                total = 0

                for record in records:
                    # Convert to string, and then parse as dates
                    # This works for all date and string fields
                    timestamp, count = record
                    total += count
                    total_dict['data'].append([timestamp, total])
                    count_dict['data'].append([timestamp, count])

                vars['graphs'].append(total_dict)
                vars['graphs'].append(count_dict)

        return vars
