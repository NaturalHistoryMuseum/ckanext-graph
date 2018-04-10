
#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-graph
# Created by the Natural History Museum in London, UK

import ckan.plugins as p
from ckan.common import _
import ckan.lib.navl.dictization_functions as df
from sqlalchemy.exc import DataError

Invalid = df.Invalid
Missing = df.Missing


def is_boolean(value, context):

    '''Validate a field as a boolean. Assuming missing value means false

    :param value: 
    :param context: 

    '''

    if isinstance(value, bool):
        return value
    elif (isinstance(value, str) or isinstance(value, unicode)) and value.lower() in [u'true', u'yes', u't', u'y', u'1']:
        return True
    elif (isinstance(value, str) or isinstance(value, unicode)) and value.lower() in [u'false', u'no', u'f', u'n', u'0']:
        return False
    elif isinstance(value, Missing):
        return False
    else:
        raise Invalid(_(u'Value must a true/false value (ie. true/yes/t/y/1 or false/no/f/n/0)'))


def in_list(list_possible_values):
    '''Validator that checks that the input value is one of the given
    possible values.

    :param list_possible_values: function that returns list of possible values
        for validated field

    '''
    def validate(key, data, errors, context):
        '''

        :param key: 
        :param data: 
        :param errors: 
        :param context: 

        '''
        if not data[key] in list_possible_values:
            raise Invalid(u'"{0}" is not a valid parameter'.format(data[key]))

    return validate


def is_date_castable(value, context):

    '''Validator to ensure the date is castable to a date field

    :param value: param context:
    :param context: 

    '''

    if value:

        sql = u'SELECT "{date_field_name}"::timestamp AS date FROM "{resource_id}" LIMIT 1 '.format(
            date_field_name=value,
            resource_id=context[u'resource'].id,
            )

        data_dict = {
            u'sql': sql
        }

        try:
            p.toolkit.get_action(u'datastore_search_sql')({}, data_dict)
        except DataError:
            raise Invalid(u'Field {0} cannot be cast into a date. Are you sure it\'s a date field?'.format(value))

    return value
