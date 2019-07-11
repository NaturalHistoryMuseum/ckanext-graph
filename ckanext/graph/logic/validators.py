# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-graph
# Created by the Natural History Museum in London, UK

from sqlalchemy.exc import DataError

from ckan.plugins import toolkit
from ckanext.graph.lib import utils


def is_boolean(value, context):
    '''Validate a field as a boolean. Assuming missing value means false

    :param value:
    :param context:

    '''

    if isinstance(value, bool):
        return value
    elif (isinstance(value, str) or isinstance(value, unicode)) and value.lower() in [
        u'true', u'yes', u't', u'y', u'1']:
        return True
    elif (isinstance(value, str) or isinstance(value, unicode)) and value.lower() in [
        u'false', u'no', u'f', u'n', u'0']:
        return False
    elif isinstance(value, type(toolkit.missing)):
        return False
    else:
        raise toolkit.Invalid(
            toolkit._(
                u'Value must a true/false value (ie. true/yes/t/y/1 or false/no/f/n/0)'))


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
            raise toolkit.Invalid(u'"{0}" is not a valid parameter'.format(data[key]))

    return validate


def is_date_castable(value, context):
    '''Validator to ensure the date is castable to a date field

    :param value:
    :param context:

    '''

    if value:
        fields = utils.get_datastore_field_types()

        field_type = fields[value]

        if field_type == u'date':
            return value
        else:
            script = u'''
            if (doc['data.{date_field_name}'].value != null) {{
             try {{
              new SimpleDateFormat('yyyy-MM-dd').parse(doc['data.{date_field_name}'].value);
              return true;
             }} catch (Exception e) {{
              return false;
             }}
            }} else {{
             return false;
            }}
            '''.format(date_field_name=value)

            data_dict = {
                u'search': {
                    u'query': {
                        u'bool': {
                            u'filter': {
                                u'script': {
                                    u'script': {
                                        u'source': script
                                        }
                                    }
                                }
                            }
                        }
                    },
                u'resource_id': toolkit.c.resource[u'id']
                }

            failure = toolkit.Invalid(
                    u'Field {0} cannot be cast into a date. Are you sure it\'s a date '
                    u'field?'.format(value))

            try:
                result = toolkit.get_action(u'datastore_search_raw')({}, data_dict)
                if result[u'total'] == 0:
                    raise failure
            except DataError:
                raise failure

    return value
