# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-graph
# Created by the Natural History Museum in London, UK

from ckan.plugins import toolkit
from sqlalchemy.exc import DataError

from ckanext.graph.lib import utils


def is_boolean(value, context):
    """
    Validate a field as a boolean. Assuming missing value means false.

    :param value:
    :param context:
    """

    if isinstance(value, bool):
        return value
    elif isinstance(value, str) and value.lower() in ['true', 'yes', 't', 'y', '1']:
        return True
    elif isinstance(value, str) and value.lower() in ['false', 'no', 'f', 'n', '0']:
        return False
    elif isinstance(value, type(toolkit.missing)):
        return False
    else:
        raise toolkit.Invalid(
            toolkit._(
                'Value must a true/false value (ie. true/yes/t/y/1 or false/no/f/n/0)'
            )
        )


def in_list(list_possible_values):
    """
    Validator that checks that the input value is one of the given possible values.

    :param list_possible_values: function that returns list of possible values for
        validated field
    """

    def validate(key, data, errors, context):
        if not data[key] in list_possible_values:
            raise toolkit.Invalid(f'"{data[key]}" is not a valid parameter')

    return validate


def is_date_castable(value, context):
    """
    Validator to ensure the date is castable to a date field.

    :param value:
    :param context:
    """

    if value:
        fields = utils.get_datastore_field_types()

        field_type = fields[value]

        if field_type == 'date':
            return value
        else:
            script = """
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
            """.format(date_field_name=value)

            data_dict = {
                'search': {
                    'query': {
                        'bool': {'filter': {'script': {'script': {'source': script}}}}
                    }
                },
                'resource_id': toolkit.c.resource['id'],
            }

            failure = toolkit.Invalid(
                f"Field {value} cannot be cast into a date. Are you sure it's a date field?"
            )

            try:
                result = toolkit.get_action('datastore_search_raw')({}, data_dict)
                if result['total'] == 0:
                    raise failure
            except DataError:
                raise failure

    return value
