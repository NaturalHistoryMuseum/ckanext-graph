from pylons import config
from sqlalchemy import create_engine
from sqlalchemy.exc import DatabaseError, DBAPIError
from beaker.cache import cache_region
from ckanext.datastore import db as datastore_db
from ckanext.datastore.helpers import is_single_statement

_read_engine = None

def _get_engine():
    """Return an SQL Alchemy engine to be used by this extention."""
    global _read_engine

    if _read_engine is None:
        _read_engine = create_engine(config['ckan.datastore.read_url'])
    return _read_engine


# @cache_region('permanent', 'stats_view_query')
def run_stats_query(select, resource_id, ts_query, where_clause, group_by, values):
    query = 'SELECT {select} FROM "{resource_id}" {ts_query} {where_clause} {group_by}'.format(
        select=select,
        resource_id=resource_id,
        where_clause=where_clause,
        ts_query=ts_query,
        group_by=group_by
    )
    print(query)

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
