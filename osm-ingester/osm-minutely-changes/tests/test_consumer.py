#!/usr/bin/env python3
import unittest
from unittest import mock
import sys
import os
import csv
import io
import time
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone

# Add parent directory to path so we can import consumer.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import consumer

class TestConsumer(unittest.TestCase):
    def setUp(self):
        # Save original environment variables
        self.original_env = {}
        for var in ['VERBOSE', 'NODES', 'WAYS', 'RELATIONS', 'MEMBERS', 'TAGS']:
            self.original_env[var] = os.environ.get(var)
        
        # Set environment variables for testing
        os.environ['VERBOSE'] = '1'
        os.environ['NODES'] = '1'
        os.environ['WAYS'] = '1'
        os.environ['RELATIONS'] = '1'
        os.environ['MEMBERS'] = '1'
        os.environ['TAGS'] = '1'
        
        # Reset max_changeset_id for each test
        consumer.max_changeset_id = 0
        
        # Update the module variables to match environment
        consumer.VERBOSE = int(os.environ['VERBOSE'])
        consumer.NODES = int(os.environ['NODES'])
        consumer.WAYS = int(os.environ['WAYS'])
        consumer.RELATIONS = int(os.environ['RELATIONS'])
        consumer.MEMBERS = int(os.environ['MEMBERS'])
        consumer.TAGS = int(os.environ['TAGS'])
    
    def tearDown(self):
        # Restore original environment variables
        for var, value in self.original_env.items():
            if value is None:
                if var in os.environ:
                    del os.environ[var]
            else:
                os.environ[var] = value

    def test_to_epoch_millis(self):
        # Test with ISO8601 string
        self.assertEqual(consumer.to_epoch_millis('2022-01-01T00:00:00Z'), 1640995200000)
        
        # Test with integer seconds
        self.assertEqual(consumer.to_epoch_millis(1640995200), 1640995200)
        
        # Test with float seconds (should convert to int milliseconds)
        self.assertEqual(consumer.to_epoch_millis(1640995200.5), 1640995200)
        
        # Test with None
        self.assertIsNone(consumer.to_epoch_millis(None))
        
        # Test with invalid string
        self.assertIsNone(consumer.to_epoch_millis('invalid-date'))

    def test_write_csv_stdout(self):
        rows = [
            {'id': '1', 'value': 'test1', 'extra': 'should_not_appear'},
            {'id': '2', 'value': 'test2'}
        ]
        fieldnames = ['id', 'value']
        
        # Capture stdout
        stdout_buffer = io.StringIO()
        with redirect_stdout(stdout_buffer):
            consumer.write_csv_stdout(rows, fieldnames)
        
        # Parse the CSV from stdout
        output = stdout_buffer.getvalue()
        csv_reader = csv.DictReader(output.strip().split('\n'))
        result_rows = list(csv_reader)
        
        # Check number of rows and row content
        self.assertEqual(len(result_rows), 2)
        self.assertEqual(result_rows[0]['id'], '1')
        self.assertEqual(result_rows[0]['value'], 'test1')
        self.assertNotIn('extra', result_rows[0])
        self.assertEqual(result_rows[1]['id'], '2')
        self.assertEqual(result_rows[1]['value'], 'test2')

    def test_process_node(self):
        # Create a mock node
        class MockNode:
            def __init__(self):
                self.attribs = {
                    'id': '123',
                    'version': '2',
                    'changeset': '456',
                    'user': 'testuser',
                    'uid': '789',
                    'lat': '51.5074',
                    'lon': '-0.1278',
                    'timestamp': '2022-01-01T00:00:00Z'
                }
        
        node = MockNode()
        nodes_rows = []
        
        # Process the node
        consumer.process_node(node, nodes_rows)
        
        # Check the result
        self.assertEqual(len(nodes_rows), 1)
        self.assertEqual(nodes_rows[0]['id'], '123')
        self.assertEqual(nodes_rows[0]['version'], '2')
        self.assertEqual(nodes_rows[0]['changeset'], '456')
        self.assertEqual(nodes_rows[0]['username'], 'testuser')
        self.assertEqual(nodes_rows[0]['uid'], '789')
        self.assertEqual(nodes_rows[0]['lat'], '51.5074')
        self.assertEqual(nodes_rows[0]['lon'], '-0.1278')
        self.assertEqual(nodes_rows[0]['epochMillis'], 1640995200000)

    def test_process_way(self):
        # Create a mock way
        class MockWay:
            def __init__(self):
                self.attribs = {
                    'id': '123',
                    'version': '2',
                    'changeset': '456',
                    'user': 'testuser',
                    'uid': '789',
                    'geometry': 'LINESTRING(0 0, 1 1)',
                    'timestamp': '2022-01-01T00:00:00Z'
                }
        
        way = MockWay()
        ways_rows = []
        
        # Process the way
        consumer.process_way(way, ways_rows)
        
        # Check the result
        self.assertEqual(len(ways_rows), 1)
        self.assertEqual(ways_rows[0]['id'], '123')
        self.assertEqual(ways_rows[0]['version'], '2')
        self.assertEqual(ways_rows[0]['changeset'], '456')
        self.assertEqual(ways_rows[0]['username'], 'testuser')
        self.assertEqual(ways_rows[0]['uid'], '789')
        self.assertEqual(ways_rows[0]['geometry'], 'LINESTRING(0 0, 1 1)')
        self.assertEqual(ways_rows[0]['epochMillis'], 1640995200000)

    def test_process_relation(self):
        # Create mock relation member
        class MockMember:
            def __init__(self, ref, role, type_):
                self.attribs = {
                    'ref': ref,
                    'role': role,
                    'type': type_
                }
        
        # Create a mock relation
        class MockRelation:
            def __init__(self):
                self.attribs = {
                    'id': '123',
                    'version': '2',
                    'changeset': '456',
                    'user': 'testuser',
                    'uid': '789',
                    'geometry': 'MULTILINESTRING((0 0, 1 1), (2 2, 3 3))',
                    'timestamp': '2022-01-01T00:00:00Z'
                }
                self.members = [
                    MockMember('456', 'outer', 'way'),
                    MockMember('789', 'inner', 'way')
                ]
        
        relation = MockRelation()
        relations_rows = []
        members_rows = []
        
        # Process the relation
        consumer.process_relation(relation, relations_rows, members_rows)
        
        # Check relation result
        self.assertEqual(len(relations_rows), 1)
        self.assertEqual(relations_rows[0]['id'], '123')
        self.assertEqual(relations_rows[0]['version'], '2')
        self.assertEqual(relations_rows[0]['changeset'], '456')
        self.assertEqual(relations_rows[0]['username'], 'testuser')
        self.assertEqual(relations_rows[0]['uid'], '789')
        self.assertEqual(relations_rows[0]['geometry'], 'MULTILINESTRING((0 0, 1 1), (2 2, 3 3))')
        self.assertEqual(relations_rows[0]['epochMillis'], 1640995200000)
        
        # Check members result
        self.assertEqual(len(members_rows), 2)
        self.assertEqual(members_rows[0]['relationId'], '123')
        self.assertEqual(members_rows[0]['memberId'], '456')
        self.assertEqual(members_rows[0]['memberRole'], 'outer')
        self.assertEqual(members_rows[0]['memberType'], 'way')
        self.assertEqual(members_rows[1]['relationId'], '123')
        self.assertEqual(members_rows[1]['memberId'], '789')
        self.assertEqual(members_rows[1]['memberRole'], 'inner')
        self.assertEqual(members_rows[1]['memberType'], 'way')

    def test_process_tags(self):
        # Replace osmdiff types with our mock classes for the duration of the test
        original_node = getattr(consumer.osmdiff, 'Node', None)
        original_way = getattr(consumer.osmdiff, 'Way', None)
        original_relation = getattr(consumer.osmdiff, 'Relation', None)
        
        # Create mock types
        class MockNodeType:
            pass
            
        class MockWayType:
            pass
            
        class MockRelationType:
            pass
        
        consumer.osmdiff.Node = MockNodeType
        consumer.osmdiff.Way = MockWayType
        consumer.osmdiff.Relation = MockRelationType
        
        try:
            # Create a mock node with tags
            class MockNode(MockNodeType):
                def __init__(self):
                    self.attribs = {
                        'id': '123',
                        'name': 'Test Node',
                        'amenity': 'restaurant',
                        'timestamp': '2022-01-01T00:00:00Z'
                    }
            
            node = MockNode()
            tags_rows = []
            
            # Process the tags
            consumer.process_tags(node, tags_rows)
            
            # Check the result
            self.assertEqual(len(tags_rows), 3)  # One for each attribute except 'id'
            
            # Check each tag
            name_tag = next(tag for tag in tags_rows if tag['key'] == 'name')
            self.assertEqual(name_tag['type'], 'node')
            self.assertEqual(name_tag['id'], '123')
            self.assertEqual(name_tag['value'], 'Test Node')
            self.assertEqual(name_tag['epochMillis'], 1640995200000)
            
            amenity_tag = next(tag for tag in tags_rows if tag['key'] == 'amenity')
            self.assertEqual(amenity_tag['type'], 'node')
            self.assertEqual(amenity_tag['id'], '123')
            self.assertEqual(amenity_tag['value'], 'restaurant')
            self.assertEqual(amenity_tag['epochMillis'], 1640995200000)
            
            timestamp_tag = next(tag for tag in tags_rows if tag['key'] == 'timestamp')
            self.assertEqual(timestamp_tag['type'], 'node')
            self.assertEqual(timestamp_tag['id'], '123')
            self.assertEqual(timestamp_tag['value'], '2022-01-01T00:00:00Z')
            self.assertEqual(timestamp_tag['epochMillis'], 1640995200000)
        finally:
            # Restore original osmdiff types
            if original_node is not None:
                consumer.osmdiff.Node = original_node
            if original_way is not None:
                consumer.osmdiff.Way = original_way
            if original_relation is not None:
                consumer.osmdiff.Relation = original_relation

    def test_output_csv_data(self):
        # Create test data for each entity type
        nodes_rows = [
            {'id': '123', 'version': '1', 'lat': '51.5074', 'lon': '-0.1278', 
             'changeset': '456', 'username': 'test', 'uid': '789', 'epochMillis': 1640995200000}
        ]
        ways_rows = [
            {'id': '456', 'version': '1', 'geometry': 'LINESTRING(0 0, 1 1)', 
             'changeset': '789', 'username': 'test', 'uid': '123', 'epochMillis': 1640995200000}
        ]
        relations_rows = [
            {'id': '789', 'version': '1', 'geometry': 'MULTILINESTRING((0 0, 1 1))', 
             'changeset': '123', 'username': 'test', 'uid': '456', 'epochMillis': 1640995200000}
        ]
        members_rows = [
            {'relationId': '789', 'memberId': '456', 'memberRole': 'outer', 'memberType': 'way'}
        ]
        tags_rows = [
            {'type': 'node', 'id': '123', 'key': 'name', 'value': 'Test', 'epochMillis': 1640995200000}
        ]
        
        # Capture stdout
        stdout_buffer = io.StringIO()
        with redirect_stdout(stdout_buffer):
            # Call the function
            consumer.output_csv_data(nodes_rows, ways_rows, relations_rows, members_rows, tags_rows)
            
        # Get the captured stdout content
        stdout_content = stdout_buffer.getvalue()
        
        # Check presence of headers for each entity type
        self.assertIn('epochMillis,id,version,changeset,username,uid,lat,lon', stdout_content)
        self.assertIn('epochMillis,id,version,changeset,username,uid,geometry', stdout_content)
        self.assertIn('relationId,memberId,memberRole,memberType', stdout_content)
        self.assertIn('epochMillis,type,id,key,value', stdout_content)
        
        # Verify some key data points are present
        self.assertIn('1640995200000,123,1,456,test,789,51.5074,-0.1278', stdout_content)
        self.assertIn('1640995200000,456,1,789,test,123,"LINESTRING(0 0, 1 1)"', stdout_content)
        self.assertIn('1640995200000,789,1,123,test,456,"MULTILINESTRING((0 0, 1 1))"', stdout_content)
        self.assertIn('789,456,outer,way', stdout_content)
        self.assertIn('1640995200000,node,123,name,Test', stdout_content)

    @mock.patch('osmdiff.AugmentedDiff')
    def test_process_diff_data(self, MockAugmentedDiff):
        # Create mocks for osmdiff types for isinstance checks
        original_node = getattr(consumer.osmdiff, 'Node', None)
        original_way = getattr(consumer.osmdiff, 'Way', None)
        original_relation = getattr(consumer.osmdiff, 'Relation', None)
        
        # Replace osmdiff types with our mock classes for the duration of the test
        class MockNodeType:
            pass
            
        class MockWayType:
            pass
            
        class MockRelationType:
            pass
        
        consumer.osmdiff.Node = MockNodeType
        consumer.osmdiff.Way = MockWayType
        consumer.osmdiff.Relation = MockRelationType
        
        try:
            # Create a mock of AugmentedDiff
            mock_adiff = mock.MagicMock()
            
            # Create mock entities for create attribute
            class MockNode(MockNodeType):
                def __init__(self, id_, changeset):
                    self.attribs = {
                        'id': id_,
                        'changeset': changeset,
                        'version': '1',
                        'user': 'testuser',
                        'uid': '123',
                        'lat': '51.5074',
                        'lon': '-0.1278',
                        'timestamp': '2022-01-01T00:00:00Z'
                    }
            
            class MockWay(MockWayType):
                def __init__(self, id_, changeset):
                    self.attribs = {
                        'id': id_,
                        'changeset': changeset,
                        'version': '1',
                        'user': 'testuser',
                        'uid': '123',
                        'geometry': 'LINESTRING(0 0, 1 1)',
                        'timestamp': '2022-01-01T00:00:00Z'
                    }
            
            class MockRelation(MockRelationType):
                def __init__(self, id_, changeset):
                    self.attribs = {
                        'id': id_,
                        'changeset': changeset,
                        'version': '1',
                        'user': 'testuser',
                        'uid': '123',
                        'geometry': 'MULTILINESTRING((0 0, 1 1))',
                        'timestamp': '2022-01-01T00:00:00Z'
                    }
                    self.members = []
            
            # Configure mock data
            node1 = MockNode('101', '1001')
            node2 = MockNode('102', '1002')
            way1 = MockWay('201', '2001')
            relation1 = MockRelation('301', '3001')
            
            mock_adiff.create = [node1, node2, way1, relation1]
            
            # Process the mock data
            nodes_rows, ways_rows, relations_rows, members_rows, tags_rows = consumer.process_diff_data(mock_adiff)
            
            # Check max_changeset_id was updated correctly
            self.assertEqual(consumer.max_changeset_id, 3001)
            
            # Check entity counts
            self.assertEqual(len(nodes_rows), 2)
            self.assertEqual(len(ways_rows), 1)
            self.assertEqual(len(relations_rows), 1)
            
            # Check specific entities
            self.assertEqual(nodes_rows[0]['id'], '101')
            self.assertEqual(nodes_rows[1]['id'], '102')
            self.assertEqual(ways_rows[0]['id'], '201')
            self.assertEqual(relations_rows[0]['id'], '301')
        finally:
            # Restore original osmdiff types
            if original_node is not None:
                consumer.osmdiff.Node = original_node
            if original_way is not None:
                consumer.osmdiff.Way = original_way
            if original_relation is not None:
                consumer.osmdiff.Relation = original_relation

    @mock.patch('consumer.process_diff_data')
    @mock.patch('osmdiff.AugmentedDiff')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('sys.argv', ['consumer.py', '12345', 'etag_output.txt'])
    def test_main(self, mock_open, MockAugmentedDiff, mock_process_diff_data):
        # Set up mock return values
        mock_process_diff_data.return_value = ([], [], [], [], [])
        
        # Configure the mock AugmentedDiff
        mock_adiff_instance = MockAugmentedDiff.return_value
        
        # Set max_changeset_id for testing
        consumer.max_changeset_id = 9999
        
        # Run the main function
        consumer.main()
        
        # Verify AugmentedDiff was configured correctly
        self.assertEqual(mock_adiff_instance.sequence_number, 12345)
        mock_adiff_instance.retrieve.assert_called_once()
        
        # Verify process_diff_data was called
        mock_process_diff_data.assert_called_once_with(mock_adiff_instance)
        
        # Verify file was opened and written correctly
        mock_open.assert_called_once_with('etag_output.txt', 'w')
        mock_open().write.assert_called_once_with('9999')


if __name__ == '__main__':
    unittest.main()