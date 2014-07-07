#!/usr/bin/env python
# encoding: utf-8
"""
Created by 'bens3' on 2013-06-21.
Copyright (c) 2013 'bens3'. All rights reserved.
"""


from ckan.common import _
import ckan.lib.navl.dictization_functions as df

Invalid = df.Invalid
Missing = df.Missing


def is_boolean(value, context):

    """Validate a field as a boolean. Assuming missing value means false"""

    if isinstance(value, bool):
        return value
    elif (isinstance(value, str) or isinstance(value, unicode)) and value.lower() in ['true', 'yes', 't', 'y', '1']:
        return True
    elif (isinstance(value, str) or isinstance(value, unicode)) and value.lower() in ['false', 'no', 'f', 'n', '0']:
        return False
    elif isinstance(value, Missing):
        return False
    else:
        raise Invalid(_('Value must a true/false value (ie. true/yes/t/y/1 or false/no/f/n/0)'))


def in_list(list_possible_values):
    '''
    Validator that checks that the input value is one of the given
    possible values.

    :param list_possible_values: function that returns list of possible values
        for validated field
    :type possible_values: function
    '''
    def validate(key, data, errors, context):
        if not data[key] in list_possible_values:
            raise Invalid('"{0}" is not a valid parameter'.format(data[key]))

    return validate