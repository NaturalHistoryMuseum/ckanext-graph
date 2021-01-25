import pytest
from ckanext.graph.lib.utils import get_datastore_field_types, get_request_query, \
    get_request_filters
from mock import MagicMock, patch


class TestGetDatastoreFieldTypes(object):
    # these tests are useful as they test the logic of the function but we should have another test
    # that puts data in the datastore and then actually uses it for the test rather than completely
    # mocking it

    def test_using_raw_fields(self):
        resource_id = MagicMock()
        search_results = {
            u'raw_fields': {
                u'field1': {
                    u'type': u'bert'
                },
                u'field2': {
                    u'type': u'flarp'
                },
                u'field3': {
                    u'keyword': u'banana'
                }
            }
        }

        mock_toolkit = MagicMock(
            c=MagicMock(resource=dict(id=resource_id)),
            get_action=MagicMock(return_value=MagicMock(return_value=search_results))
        )

        with patch(u'ckanext.graph.lib.utils.toolkit', mock_toolkit):
            field_types = get_datastore_field_types()

        assert len(field_types) == 3
        assert field_types[u'field1'] == u'bert'
        assert field_types[u'field2'] == u'flarp'
        assert field_types[u'field3'] == u'keyword'

    def test_using_fields(self):
        resource_id = MagicMock()
        search_results = {
            u'fields': {
                u'field1': {
                    u'type': u'bert'
                },
                u'field2': {
                    u'type': u'flarp'
                },
                u'field3': {
                    u'keyword': u'banana'
                }
            }
        }

        mock_toolkit = MagicMock(
            c=MagicMock(resource=dict(id=resource_id)),
            get_action=MagicMock(return_value=MagicMock(return_value=search_results))
        )

        with patch(u'ckanext.graph.lib.utils.toolkit', mock_toolkit):
            field_types = get_datastore_field_types()

        assert len(field_types) == 3
        assert field_types[u'field1'] == u'bert'
        assert field_types[u'field2'] == u'flarp'
        assert field_types[u'field3'] == u'keyword'

    def test_no_fields(self):
        resource_id = MagicMock()
        search_results = {}

        mock_toolkit = MagicMock(
            c=MagicMock(resource=dict(id=resource_id)),
            get_action=MagicMock(return_value=MagicMock(return_value=search_results))
        )

        with patch(u'ckanext.graph.lib.utils.toolkit', mock_toolkit):
            field_types = get_datastore_field_types()

        assert len(field_types) == 0


class TestGetRequestQuery(object):

    def test_simple(self, test_request_context):
        with test_request_context(u'/?q=beans'):
            assert get_request_query() == u'beans'

    def test_missing(self, test_request_context):
        with test_request_context(u'/?lemons=yes'):
            assert get_request_query() == u''


class TestGetRequestFilters(object):

    def test_missing(self, test_request_context):
        with test_request_context(u'/?lemons=beans'):
            filters = get_request_filters()
        assert filters == {}

    def test_simple(self, test_request_context):
        with test_request_context(u'/?filters=beans:4|lemons:yes|goats:always'):
            filters = get_request_filters()

        assert len(filters) == 3
        assert filters[u'beans'] == [u'4']
        assert filters[u'lemons'] == [u'yes']
        assert filters[u'goats'] == [u'always']

    def test_multiples(self, test_request_context):
        with test_request_context(u'/?filters=beans:4|goats:yes|beans:some'):
            filters = get_request_filters()

        assert len(filters) == 2
        assert filters[u'beans'] == [u'4', u'some']
        assert filters[u'goats'] == [u'yes']

    def test_colon(self, test_request_context):
        with test_request_context(u'/?filters=beans:4:4:2|goats:yes'):
            filters = get_request_filters()

        assert len(filters) == 2
        assert filters[u'beans'] == [u'4:4:2']
        assert filters[u'goats'] == [u'yes']
