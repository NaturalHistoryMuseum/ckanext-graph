#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-graph
# Created by the Natural History Museum in London, UK
from urllib.parse import unquote

from ckan.plugins import toolkit


def get_datastore_field_types():
    """
    Get a dict of datastore field names and their types.

    :return: a dict of {field_name: field_type}
    """
    data = {
        'resource_id': toolkit.c.resource['id'],
        'limit': 0,
    }
    results = toolkit.get_action('datastore_search')({}, data)
    fields = results.get('raw_fields', results.get('fields', {}))

    return {k: v.get('type', 'keyword') for k, v in fields.items()}


def get_request_filters():
    """
    Retrieve filters from the URL parameters and return them as a dict.

    :return: a dict of {field_name: [filter1,filter2,...]}
    """
    filters = {}
    for f in unquote(toolkit.request.params.get('filters', '')).split('|'):
        if f:
            k, v = f.split(':', 1)
            if k not in filters:
                filters[k] = []
            filters[k].append(v)
    return filters


def get_request_query():
    """
    Retrieve the q parameter from the URL and return unquoted.

    :return: string
    """
    q = unquote(toolkit.request.params.get('q', ''))
    return q if q and q != '' else None
