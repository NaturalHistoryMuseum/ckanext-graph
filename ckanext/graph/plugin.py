import pylons
import urllib
import logging
import datetime
import dateutil.parser
from sqlalchemy.exc import DatabaseError, DBAPIError
from beaker.cache import cache_region

import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions as df
import ckan.logic as logic
from ckan.common import request

from ckanext.datastore import interfaces
from ckanext.datastore import db as datastore_db
from ckanext.datastore.helpers import is_single_statement

from ckanext.graph.logic.validators import is_boolean, in_list, is_date_castable
from ckanext.graph.db import _get_engine

get_action = logic.get_action

not_empty = p.toolkit.get_validator('not_empty')
ignore_empty = p.toolkit.get_validator('ignore_empty')

log = logging.getLogger(__name__)

Invalid = df.Invalid
Missing = df.Missing

DATE_INTERVALS = ['minute', 'hour', 'day', 'month', 'year']

# List of field types that can be cast to date and used in the temporal query
TEMPORAL_FIELD_TYPES = ['text', 'timestamp', 'date', 'citext']

class GraphPlugin(p.SingletonPlugin):
    """
    Gallery plugin
    """
    p.implements(p.IConfigurer)
    p.implements(p.IResourceView, inherit=True)
    p.implements(interfaces.IDatastore, inherit=True)
    datastore_field_names = []

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
                'show_date': [is_boolean],
                'date_field': [ignore_empty, is_date_castable, in_list(self.datastore_field_names)],
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

    def _query(self, context, select, resource_id, group_by=''):

        # Build a data dict, ready to pass through to datastore interfaces
        data_dict = {
            'connection_url': pylons.config['ckan.datastore.write_url'],
            'resource_id': resource_id,
            'filters': self._get_request_filters(),
            'q': urllib.unquote(request.params.get('q', ''))
        }

        field_types = self._get_datastore_fields(resource_id)

        (ts_query, where_clause, values) = self._get_request_where_clause(data_dict, field_types)
        # Prepare and run our query
        @cache_region('permanent', 'stats_view_query')
        def run_stats_query(select, resource_id, ts_query, where_clause, group_by):
            query = 'SELECT {select} FROM "{resource_id}" {ts_query} {where_clause} {group_by}'.format(
                select=select,
                resource_id=resource_id,
                where_clause=where_clause,
                ts_query=ts_query,
                group_by=group_by
            )

            if not is_single_statement(query):
                raise datastore_db.ValidationError({
                    'query': ['Query is not a single statement.']
                })

            # The interfaces.IDatastore return SQL to be directly executed
            # So just use an sqlalchemy connection, rather than the API
            # So we don't have to faff around converting to pure SQL
            engine = _get_engine()
            with engine.begin() as connection:
                try:
                    query_result = connection.execute(query, values)
                    return query_result.fetchall()
                except (DatabaseError, DBAPIError):
                    pass
        return run_stats_query(select, resource_id, ts_query, where_clause, group_by)


    def _get_request_where_clause(self, data_dict, field_types):
        """Return the where clause that applies to a query matching the given request

        @param data_dict: A dictionary representing a datastore API request
        @param field_types: A dictionary of field name to field type. Must
                            include all the fields that may be used in the
                            query
        @return: Tuple defining (
                    extra from statement for full text queries,
                    where clause,
                    list of replacement values
                )
        """
        query_dict = {
            'select': [],
            'sort': [],
            'where': []
        }

        for plugin in p.PluginImplementations(interfaces.IDatastore):
            query_dict = plugin.datastore_search(
                {}, data_dict, field_types, query_dict
            )

        clauses = []
        values = []

        for clause_and_values in query_dict['where']:
            clauses.append('(' + clause_and_values[0] + ')')
            values += clause_and_values[1:]

        where_clause = u' AND '.join(clauses)
        if where_clause:
            where_clause = u'WHERE ' + where_clause

        if 'ts_query' in query_dict and query_dict['ts_query']:
            ts_query = query_dict['ts_query']
        else:
            ts_query = ''

        return ts_query, where_clause, values


    def _get_request_filters(self):
        """Return a dict representing the filters of the current request"""
        filters = {}
        for f in urllib.unquote(request.params.get('filters', '')).split('|'):
            if f:
                (k, v) = f.split(':', 1)
                if k not in filters:
                    filters[k] = []
                filters[k].append(v)
        return filters

    def setup_template_variables(self, context, data_dict):
        """
        Setup variables available to templates
        """

        datastore_fields = self._get_datastore_fields(data_dict['resource']['id'])

        self.datastore_field_names = datastore_fields.keys()

        vars = {
            'count_field_options':  [None] + [{'value': field_name, 'text': field_name} for field_name, field_type in datastore_fields.items()],
            'date_field_options': [None] + [{'value': field_name, 'text': field_name} for field_name, field_type in datastore_fields.items() if field_type in TEMPORAL_FIELD_TYPES],
            'date_interval_options': [{'value': interval, 'text': interval} for interval in DATE_INTERVALS],
            'defaults': {},
            'graphs': [],
            'resource': data_dict['resource']
        }

        if data_dict['resource_view'].get('show_count', None) and data_dict['resource_view'].get('count_field', None):

            count_field = data_dict['resource_view'].get('count_field')

            select = '{count_field} as fld, count ({count_field}) as count'.format(
                count_field=count_field
            )

            records = self._query(context, select, data_dict['resource']['id'], group_by='GROUP BY %s ORDER BY count DESC LIMIT 25' % count_field)

            if records:

                count_dict = {
                    'title': data_dict['resource_view'].get('count_label', None) or count_field,
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

        # Do we want a date statistics graph
        if data_dict['resource_view'].get('show_date', None) and data_dict['resource_view'].get('date_field', None):

            date_interval = data_dict['resource_view'].get('date_interval')

            select = 'date_trunc(\'{date_interval}\', "{date_field}"::timestamp) AS date, COUNT(*) AS count'.format(
                date_interval=date_interval,
                date_field=data_dict['resource_view'].get('date_field')
            )

            records = self._query(context, select, data_dict['resource']['id'], group_by='GROUP BY 1 ORDER BY 1')

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
                                'align': "center"
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
                    date = dateutil.parser.parse(str(record['date']))
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

        field_types = dict([(f['id'], f['type']) for f in fields])
        field_types['_id'] = 'int'

        return field_types

def _get_records_from_datastore(resource, limit, offset):
    data = {'resource_id': resource['id']}
    if limit:
        data['limit'] = limit
    if offset:
        data['offset'] = offset
    records = p.toolkit.get_action('datastore_search')({}, data)['records']
    return records
