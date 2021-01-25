#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-graph
# Created by the Natural History Museum in London, UK

import urllib

from ckan.plugins import toolkit


def get_datastore_field_types():
    '''
    Get a dict of datastore field names and their types.
    :return: a dict of {field_name: field_type}
    '''
    data = {
        u'resource_id': toolkit.c.resource[u'id'],
        u'limit': 0,
        }
    results = toolkit.get_action(u'datastore_search')({}, data)
    fields = results.get(u'raw_fields', results.get(u'fields', {}))

    return {k: v.get(u'type', u'keyword') for k, v in fields.items()}


def get_request_filters():
    '''
    Retrieve filters from the URL parameters and return them as a dict.
    :return: a dict of {field_name: [filter1,filter2,...]}
    '''
    filters = {}
    for f in urllib.unquote(toolkit.request.params.get(u'filters', u'')).split(u'|'):
        if f:
            k, v = f.split(u':', 1)
            if k not in filters:
                filters[k] = []
            filters[k].append(v)
    return filters


def get_request_query():
    '''
    Retrieve the q parameter from the URL and return unquoted.
    :return: string
    '''
    return urllib.unquote(toolkit.request.params.get(u'q', u''))
