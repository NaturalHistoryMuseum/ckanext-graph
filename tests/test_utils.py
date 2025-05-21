from unittest.mock import MagicMock, patch

from ckanext.graph.lib.utils import (
    get_datastore_field_types,
    get_request_filters,
    get_request_query,
)


class TestGetDatastoreFieldTypes(object):
    # these tests are useful as they test the logic of the function but we should have another test
    # that puts data in the datastore and then actually uses it for the test rather than completely
    # mocking it

    def test_using_fields(self):
        resource_id = MagicMock()
        search_results = {
            'fields': {
                'field1': {'type': 'bert'},
                'field2': {'type': 'flarp'},
                'field3': {'keyword': 'banana'},
            }
        }

        mock_toolkit = MagicMock(
            c=MagicMock(resource=dict(id=resource_id)),
            get_action=MagicMock(return_value=MagicMock(return_value=search_results)),
        )

        with patch('ckanext.graph.lib.utils.toolkit', mock_toolkit):
            field_types = get_datastore_field_types()

        assert len(field_types) == 3
        assert field_types['field1'] == 'bert'
        assert field_types['field2'] == 'flarp'
        assert field_types['field3'] == 'keyword'

    def test_no_fields(self):
        resource_id = MagicMock()
        search_results = {}

        mock_toolkit = MagicMock(
            c=MagicMock(resource=dict(id=resource_id)),
            get_action=MagicMock(return_value=MagicMock(return_value=search_results)),
        )

        with patch('ckanext.graph.lib.utils.toolkit', mock_toolkit):
            field_types = get_datastore_field_types()

        assert len(field_types) == 0


class TestGetRequestQuery(object):
    def test_simple(self, test_request_context):
        with test_request_context('/?q=beans'):
            assert get_request_query() == 'beans'

    def test_missing(self, test_request_context):
        with test_request_context('/?lemons=yes'):
            assert get_request_query() is None


class TestGetRequestFilters(object):
    def test_missing(self, test_request_context):
        with test_request_context('/?lemons=beans'):
            filters = get_request_filters()
        assert filters == {}

    def test_simple(self, test_request_context):
        with test_request_context('/?filters=beans:4|lemons:yes|goats:always'):
            filters = get_request_filters()

        assert len(filters) == 3
        assert filters['beans'] == ['4']
        assert filters['lemons'] == ['yes']
        assert filters['goats'] == ['always']

    def test_multiples(self, test_request_context):
        with test_request_context('/?filters=beans:4|goats:yes|beans:some'):
            filters = get_request_filters()

        assert len(filters) == 2
        assert filters['beans'] == ['4', 'some']
        assert filters['goats'] == ['yes']

    def test_colon(self, test_request_context):
        with test_request_context('/?filters=beans:4:4:2|goats:yes'):
            filters = get_request_filters()

        assert len(filters) == 2
        assert filters['beans'] == ['4:4:2']
        assert filters['goats'] == ['yes']
