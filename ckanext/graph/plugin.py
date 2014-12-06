import re
import ckan.plugins as p
from ckan.common import json
import ckan.plugins.toolkit as toolkit
import ckan.model as model
from ckan.common import _, c
import ckan.lib.navl.dictization_functions as df
import ckan.logic as logic
import dateutil.parser
import datetime
from ckanext.datastore.interfaces import IDatastore
from ckanext.graph.logic.validators import is_boolean, in_list, is_date_castable
import logging
from ckan.common import json, request, _, response
from sqlalchemy.exc import DataError
get_action = logic.get_action

not_empty = p.toolkit.get_validator('not_empty')
ignore_empty = p.toolkit.get_validator('ignore_empty')

log = logging.getLogger(__name__)

Invalid = df.Invalid
Missing = df.Missing

DATE_INTERVALS = ['minute', 'hour', 'day', 'month', 'year']

class GraphPlugin(p.SingletonPlugin):
    """
    Gallery plugin
    """
    p.implements(p.IConfigurer)
    p.implements(p.IResourceView, inherit=True)
    p.implements(IDatastore, inherit=True)

    datastore_fields = []

    ## IConfigurer
    def update_config(self, config):
        """Add our template directories to the list of available templates"""
        p.toolkit.add_template_directory(config, 'theme/templates')
        p.toolkit.add_public_directory(config, 'theme/public')
        p.toolkit.add_resource('theme/public', 'ckanext-graph')

    ## IResourceView
    def info(self):
        """Return generic info about the plugin"""
        return {
            'name': 'graph',
            'title': 'Graph',
            'schema': {
                'temporal': [is_boolean],
                'date_field': [not_empty, in_list(self.list_datastore_fields()), is_date_castable],
                'date_interval': [not_empty, in_list(DATE_INTERVALS)],
                'count_field': [is_boolean],
                'count_field_label': [],
                'count_field_name': [not_empty, in_list(self.list_datastore_fields())],
            },
            'icon': 'bar-chart',
            'iframed': False,
            'filterable': True,
            'preview_enabled': False,
            'full_page_edit': False
        }

    # IDatastore
    def datastore_search(self, context, data_dict, all_field_ids, query_dict):
        return query_dict

    def datastore_validate(self, context, data_dict, all_field_ids):
        return data_dict

    def view_template(self, context, data_dict):
        return 'graph/view.html'

    def form_template(self, context, data_dict):
        return 'graph/form.html'

    def can_view(self, data_dict):
        """Specify which resources can be viewed by this plugin"""
        # Check that we have a datastore for this resource
        if data_dict['resource'].get('datastore_active'):
            return True
        return False

    @staticmethod
    def _query(select, resource_id, group_by=''):

        # Add filters from request

        where = []

        filter_str = request.params.get('filters')

        if filter_str:
            for f in filter_str.split('|'):
                try:
                    (field, value) = f.split(':')

                    if field != '_f':
                        where.append('"{field}" = \'{value}\''.format(field=field, value=value))

                except ValueError:
                    pass

        # Full text filter
        fulltext = request.params.get('q')

        if fulltext:
            where.append('_full_text @@ plainto_tsquery(\'{fulltext}\')'.format(fulltext=fulltext))

        data_dict = {
            'sql': '{select} FROM "{resource_id}" {where} {group_by}'.format(
                select=select,
                resource_id=resource_id,
                where='WHERE %s' % ' AND '.join(where) if where else '',
                group_by=group_by
                )
            }

        try:
            return p.toolkit.get_action('datastore_search_sql')({}, data_dict)['records']
        except (DataError, toolkit.ValidationError), e:
            log.critical(e)

    def setup_template_variables(self, context, data_dict):
        """Setup variables available to templates"""
        self.datastore_fields = self._get_datastore_fields(data_dict['resource']['id'])

        vars = {
            'datastore_field_options':  self.datastore_fields,
            'date_interval_options': [{'value': interval, 'text': interval} for interval in DATE_INTERVALS],
            'defaults': {},
            'graphs': [],
            'resource': data_dict['resource']
        }

        if data_dict['resource_view'].get('count_field', None):

            field_name = data_dict['resource_view'].get('count_field_name')

            select = 'select {field_name} as fld, count ({field_name}) as count'.format(
                field_name=field_name
            )

            records = self._query(select, data_dict['resource']['id'], group_by='GROUP BY %s ORDER BY count DESC LIMIT 25' % field_name)

            if records:

                count_dict = {
                    'title': data_dict['resource_view'].get('count_field_label', None) or field_name,
                    'data': [],
                    'options': {
                        'bars': {
                            'show': True,
                            'barWidth': 0.6,
                            'align': "center"
                        },
                        'xaxis': {
                            'ticks': [],
                            'rotateTicks': 60,
                        }
                    }
                }

                for i, record in enumerate(records):
                    count_dict['data'].append([i, record['count']])
                    count_dict['options']['xaxis']['ticks'].append([i, record['fld']])

                vars['graphs'].append(count_dict)

        # We we have a statistics graph
        if data_dict['resource_view'].get('temporal', None):

            date_interval = data_dict['resource_view'].get('date_interval')

            select = 'SELECT date_trunc(\'{date_interval}\', "{date_field}"::timestamp) AS date, COUNT(*) AS count'.format(
                date_interval=date_interval,
                date_field=data_dict['resource_view'].get('date_field')
            )

            records = self._query(select, data_dict['resource']['id'], group_by='GROUP BY 1 ORDER BY 1')

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
                            'lines': {'show': True},
                            'points': {'show': True}
                            }
                        }
                }

                count_dict = {
                    'title': 'Per %s' % date_interval,
                    'data': [],
                    'options': {
                        'series': {
                            'bars': {
                                'show': True,
                                'barWidth': 0.6,
                                'align': "center"
                            }
                        }
                    }
                }

                total_dict['options'].update(default_options)
                count_dict['options'].update(default_options)

                total = 0

                for record in records:
                    date = dateutil.parser.parse(record['date'])
                    count = int(record['count'])

                    label = int((date - datetime.datetime(1970, 1, 1)).total_seconds()*1000)

                    total += count

                    total_dict['data'].append([label, total])
                    count_dict['data'].append([label, count])

                vars['graphs'].append(total_dict)
                vars['graphs'].append(count_dict)

        return vars

    def _get_datastore_fields(self, resource_id):
        data = {'resource_id': resource_id, 'limit': 0}
        fields = toolkit.get_action('datastore_search')({}, data)['fields']
        return [{'value': f['id'], 'text': f['id']} for f in fields]

    def list_datastore_fields(self):
        return [t['value'] for t in self.datastore_fields]

def _get_records_from_datastore(resource, limit, offset):
    data = {'resource_id': resource['id']}
    if limit:
        data['limit'] = limit
    if offset:
        data['offset'] = offset
    records = p.toolkit.get_action('datastore_search')({}, data)['records']
    return records
