#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-graph
# Created by the Natural History Museum in London, UK

from beaker.cache import cache_region
from ckanext.datastore import backend as datastore_db
from sqlalchemy import create_engine
from sqlalchemy.exc import DBAPIError, DatabaseError

from ckan.plugins import toolkit
from ckanext.datastore.helpers import is_single_statement

_read_engine = None


def _get_engine():
    ''' '''
    global _read_engine

    if _read_engine is None:
        _read_engine = create_engine(toolkit.config[u'ckan.datastore.read_url'])
    return _read_engine


@cache_region(u'permanent', u'stats_view_query')
def run_stats_query(select, resource_id, ts_query, where_clause, group_by, values):
    '''

    :param select: 
    :param resource_id: 
    :param ts_query: 
    :param where_clause: 
    :param group_by: 
    :param values: 

    '''
    query = u'SELECT {select} ' \
            u'FROM "{resource_id}" {ts_query} ' \
            u'{where_clause} {group_by}'.format(select=select,
                                                resource_id=resource_id,
                                                where_clause=where_clause,
                                                ts_query=ts_query,
                                                group_by=group_by)

    if not is_single_statement(query):
        raise datastore_db.ValidationError({
            u'query': [u'Query is not a single statement.']
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
