# -*- coding: utf-8 -*-
import os
import sys
import csv
import time
import click
import threading
from RLTest import Env
from click.testing import CliRunner
from redisgraph_bulk_loader.bulk_insert import bulk_insert

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from redisgraph import Graph, Node, Edge
from base import FlowTestsBase

redis_con = None
port = None
redis_graph = None

def run_bulk_loader(graphname, filename):
    runner = CliRunner()
    runner.invoke(bulk_insert, ['--port', port,
                                '--nodes', filename,
                                graphname])

class testGraphBulkInsertFlow(FlowTestsBase):
    def __init__(self):
        self.env = Env(decodeResponses=True)
        global redis_graph
        global redis_con
        redis_con = self.env.getConnection()
        port = self.env.envRunner.port
        redis_graph = Graph("graph", redis_con)

    # Run bulk loader script and validate terminal output
    def test01_run_script(self):
        graphname = "graph"
        runner = CliRunner()

        csv_path = os.path.dirname(os.path.abspath(__file__)) + '/../../demo/social/resources/bulk_formatted/'
        res = runner.invoke(bulk_insert, ['--port', port,
                                          '--nodes', csv_path + 'Person.csv',
                                          '--nodes', csv_path + 'Country.csv',
                                          '--relations', csv_path + 'KNOWS.csv',
                                          '--relations', csv_path + 'VISITED.csv',
                                          graphname])

        # The script should report 27 node creations and 48 edge creations
        self.env.assertEquals(res.exit_code, 0)
        self.env.assertIn('27 nodes created', res.output)
        self.env.assertIn('56 relations created', res.output)

    # Validate that the expected nodes and properties have been constructed
    def test02_validate_nodes(self):
        global redis_graph
        # Query the newly-created graph
        query_result = redis_graph.query('MATCH (p:Person) RETURN p.name, p.age, p.gender, p.status, ID(p) ORDER BY p.name')
        # Verify that the Person label exists, has the correct attributes, and is properly populated
        expected_result = [['Ailon Velger', 32, 'male', 'married', 2],
                           ['Alon Fital', 32, 'male', 'married', 1],
                           ['Boaz Arad', 31, 'male', 'married', 4],
                           ['Gal Derriere', 26, 'male', 'single', 11],
                           ['Jane Chernomorin', 31, 'female', 'married', 8],
                           ['Lucy Yanfital', 30, 'female', 'married', 7],
                           ['Mor Yesharim', 31, 'female', 'married', 12],
                           ['Noam Nativ', 34, 'male', 'single', 13],
                           ['Omri Traub', 33, 'male', 'single', 5],
                           ['Ori Laslo', 32, 'male', 'married', 3],
                           ['Roi Lipman', 32, 'male', 'married', 0],
                           ['Shelly Laslo Rooz', 31, 'female', 'married', 9],
                           ['Tal Doron', 32, 'male', 'single', 6],
                           ['Valerie Abigail Arad', 31, 'female', 'married', 10]]
        self.env.assertEquals(query_result.result_set, expected_result)

        # Verify that the Country label exists, has the correct attributes, and is properly populated
        query_result = redis_graph.query('MATCH (c:Country) RETURN c.name, ID(c) ORDER BY c.name')
        expected_result = [['Andora', 21],
                           ['Canada', 18],
                           ['China', 19],
                           ['Germany', 24],
                           ['Greece', 17],
                           ['Italy', 25],
                           ['Japan', 16],
                           ['Kazakhstan', 22],
                           ['Netherlands', 20],
                           ['Prague', 15],
                           ['Russia', 23],
                           ['Thailand', 26],
                           ['USA', 14]]
        self.env.assertEquals(query_result.result_set, expected_result)

    # Validate that the expected relations and properties have been constructed
    def test03_validate_relations(self):
        # Query the newly-created graph
        query_result = redis_graph.query('MATCH (a)-[e:KNOWS]->(b) RETURN a.name, e.relation, b.name ORDER BY e.relation, a.name, b.name')

        expected_result = [['Ailon Velger', 'friend', 'Noam Nativ'],
                           ['Alon Fital', 'friend', 'Gal Derriere'],
                           ['Alon Fital', 'friend', 'Mor Yesharim'],
                           ['Boaz Arad', 'friend', 'Valerie Abigail Arad'],
                           ['Roi Lipman', 'friend', 'Ailon Velger'],
                           ['Roi Lipman', 'friend', 'Alon Fital'],
                           ['Roi Lipman', 'friend', 'Boaz Arad'],
                           ['Roi Lipman', 'friend', 'Omri Traub'],
                           ['Roi Lipman', 'friend', 'Ori Laslo'],
                           ['Roi Lipman', 'friend', 'Tal Doron'],
                           ['Ailon Velger', 'married', 'Jane Chernomorin'],
                           ['Alon Fital', 'married', 'Lucy Yanfital'],
                           ['Ori Laslo', 'married', 'Shelly Laslo Rooz']]
        self.env.assertEquals(query_result.result_set, expected_result)

        query_result = redis_graph.query('MATCH (a)-[e:VISITED]->(b) RETURN a.name, e.purpose, b.name ORDER BY e.purpose, a.name, b.name')

        expected_result = [['Alon Fital', 'business', 'Prague'],
                           ['Alon Fital', 'business', 'USA'],
                           ['Boaz Arad', 'business', 'Netherlands'],
                           ['Boaz Arad', 'business', 'USA'],
                           ['Gal Derriere', 'business', 'Netherlands'],
                           ['Jane Chernomorin', 'business', 'USA'],
                           ['Lucy Yanfital', 'business', 'USA'],
                           ['Mor Yesharim', 'business', 'Germany'],
                           ['Ori Laslo', 'business', 'China'],
                           ['Ori Laslo', 'business', 'USA'],
                           ['Roi Lipman', 'business', 'Prague'],
                           ['Roi Lipman', 'business', 'USA'],
                           ['Tal Doron', 'business', 'Japan'],
                           ['Tal Doron', 'business', 'USA'],
                           ['Alon Fital', 'pleasure', 'Greece'],
                           ['Alon Fital', 'pleasure', 'Prague'],
                           ['Alon Fital', 'pleasure', 'USA'],
                           ['Boaz Arad', 'pleasure', 'Netherlands'],
                           ['Boaz Arad', 'pleasure', 'USA'],
                           ['Jane Chernomorin', 'pleasure', 'Greece'],
                           ['Jane Chernomorin', 'pleasure', 'Netherlands'],
                           ['Jane Chernomorin', 'pleasure', 'USA'],
                           ['Lucy Yanfital', 'pleasure', 'Kazakhstan'],
                           ['Lucy Yanfital', 'pleasure', 'Prague'],
                           ['Lucy Yanfital', 'pleasure', 'USA'],
                           ['Mor Yesharim', 'pleasure', 'Greece'],
                           ['Mor Yesharim', 'pleasure', 'Italy'],
                           ['Noam Nativ', 'pleasure', 'Germany'],
                           ['Noam Nativ', 'pleasure', 'Netherlands'],
                           ['Noam Nativ', 'pleasure', 'Thailand'],
                           ['Omri Traub', 'pleasure', 'Andora'],
                           ['Omri Traub', 'pleasure', 'Greece'],
                           ['Omri Traub', 'pleasure', 'USA'],
                           ['Ori Laslo', 'pleasure', 'Canada'],
                           ['Roi Lipman', 'pleasure', 'Japan'],
                           ['Roi Lipman', 'pleasure', 'Prague'],
                           ['Shelly Laslo Rooz', 'pleasure', 'Canada'],
                           ['Shelly Laslo Rooz', 'pleasure', 'China'],
                           ['Shelly Laslo Rooz', 'pleasure', 'USA'],
                           ['Tal Doron', 'pleasure', 'Andora'],
                           ['Tal Doron', 'pleasure', 'USA'],
                           ['Valerie Abigail Arad', 'pleasure', 'Netherlands'],
                           ['Valerie Abigail Arad', 'pleasure', 'Russia']]
        self.env.assertEquals(query_result.result_set, expected_result)

    def test04_private_identifiers(self):
        graphname = "tmpgraph1"
        # Write temporary files
        with open('/tmp/nodes.tmp', mode='w') as csv_file:
            out = csv.writer(csv_file)
            out.writerow(["_identifier", "nodename"])
            out.writerow([0, "a"])
            out.writerow([5, "b"])
            out.writerow([3, "c"])
        with open('/tmp/relations.tmp', mode='w') as csv_file:
            out = csv.writer(csv_file)
            out.writerow(["src", "dest"])
            out.writerow([0, 3])
            out.writerow([5, 3])

        runner = CliRunner()
        res = runner.invoke(bulk_insert, ['--port', port,
                                          '--nodes', '/tmp/nodes.tmp',
                                          '--relations', '/tmp/relations.tmp',
                                          graphname])

        # The script should report 3 node creations and 2 edge creations
        self.env.assertEquals(res.exit_code, 0)
        self.env.assertIn('3 nodes created', res.output)
        self.env.assertIn('2 relations created', res.output)

        # Delete temporary files
        os.remove('/tmp/nodes.tmp')
        os.remove('/tmp/relations.tmp')

        tmp_graph = Graph(graphname, redis_con)
        # The field "_identifier" should not be a property in the graph
        query_result = tmp_graph.query('MATCH (a) RETURN a')

        for propname in query_result.header:
            self.env.assertNotIn('_identifier', propname)

    def test05_reused_identifier(self):
        graphname = "tmpgraph2"
        # Write temporary files
        with open('/tmp/nodes.tmp', mode='w') as csv_file:
            out = csv.writer(csv_file)
            out.writerow(["_identifier", "nodename"])
            out.writerow([0, "a"])
            out.writerow([5, "b"])
            out.writerow([0, "c"]) # reused identifier
        with open('/tmp/relations.tmp', mode='w') as csv_file:
            out = csv.writer(csv_file)
            out.writerow(["src", "dest"])
            out.writerow([0, 3])

        runner = CliRunner()
        res = runner.invoke(bulk_insert, ['--port', port,
                                          '--nodes', '/tmp/nodes.tmp',
                                          '--relations', '/tmp/relations.tmp',
                                          graphname])

        # The script should fail because a node identifier is reused
        self.env.assertNotEqual(res.exit_code, 0)
        self.env.assertIn('used multiple times', res.output)

        # Run the script again without creating relations
        runner = CliRunner()
        res = runner.invoke(bulk_insert, ['--port', port,
                                          '--nodes', '/tmp/nodes.tmp',
                                          graphname])

        # The script should succeed and create 3 nodes
        self.env.assertEquals(res.exit_code, 0)
        self.env.assertIn('3 nodes created', res.output)

        # Delete temporary files
        os.remove('/tmp/nodes.tmp')
        os.remove('/tmp/relations.tmp')

    def test06_batched_build(self):
        # Create demo graph wth one query per input file
        graphname = "batched_graph"
        runner = CliRunner()

        csv_path = os.path.dirname(os.path.abspath(__file__)) + '/../../demo/social/resources/bulk_formatted/'
        res = runner.invoke(bulk_insert, ['--port', port,
                                          '--nodes', csv_path + 'Person.csv',
                                          '--nodes', csv_path + 'Country.csv',
                                          '--relations', csv_path + 'KNOWS.csv',
                                          '--relations', csv_path + 'VISITED.csv',
                                          '--max-token-count', 1,
                                          graphname])

        self.env.assertEquals(res.exit_code, 0)
        # The script should report statistics multiple times
        self.env.assertGreater(res.output.count('nodes created'), 1)

        new_graph = Graph(graphname, redis_con)

        # Newly-created graph should be identical to graph created in single query
        original_result = redis_graph.query('MATCH (p:Person) RETURN p, ID(p) ORDER BY p.name')
        new_result = new_graph.query('MATCH (p:Person) RETURN p, ID(p) ORDER BY p.name')
        self.env.assertEquals(original_result.result_set, new_result.result_set)

        original_result = redis_graph.query('MATCH (a)-[e:KNOWS]->(b) RETURN a.name, e, b.name ORDER BY e.relation, a.name')
        new_result = new_graph.query('MATCH (a)-[e:KNOWS]->(b) RETURN a.name, e, b.name ORDER BY e.relation, a.name')
        self.env.assertEquals(original_result.result_set, new_result.result_set)

    def test07_script_failures(self):
        graphname = "tmpgraph3"
        # Write temporary files
        with open('/tmp/nodes.tmp', mode='w') as csv_file:
            out = csv.writer(csv_file)
            out.writerow(["id", "nodename"])
            out.writerow([0]) # Wrong number of properites

        runner = CliRunner()
        res = runner.invoke(bulk_insert, ['--port', port,
                                          '--nodes', '/tmp/nodes.tmp',
                                          graphname])

        # The script should fail because a row has the wrong number of fields
        self.env.assertNotEqual(res.exit_code, 0)
        self.env.assertIn('Expected 2 columns', str(res.exception))

        # Write temporary files
        with open('/tmp/nodes.tmp', mode='w') as csv_file:
            out = csv.writer(csv_file)
            out.writerow(["id", "nodename"])
            out.writerow([0, "a"])

        with open('/tmp/relations.tmp', mode='w') as csv_file:
            out = csv.writer(csv_file)
            out.writerow(["src"]) # Incomplete relation description
            out.writerow([0])

        runner = CliRunner()
        res = runner.invoke(bulk_insert, ['--port', port,
                                          '--nodes', '/tmp/nodes.tmp',
                                          '--relations', '/tmp/relations.tmp',
                                          graphname])

        # The script should fail because a row has the wrong number of fields
        self.env.assertNotEqual(res.exit_code, 0)
        self.env.assertIn('should have at least 2 elements', str(res.exception))

        with open('/tmp/relations.tmp', mode='w') as csv_file:
            out = csv.writer(csv_file)
            out.writerow(["src", "dest"])
            out.writerow([0, "fakeidentifier"])

        runner = CliRunner()
        res = runner.invoke(bulk_insert, ['--port', port,
                                          '--nodes', '/tmp/nodes.tmp',
                                          '--relations', '/tmp/relations.tmp',
                                          graphname])

        # The script should fail because an invalid node identifier was used
        self.env.assertNotEqual(res.exit_code, 0)
        self.env.assertIn('fakeidentifier', str(res.exception))
        os.remove('/tmp/nodes.tmp')
        os.remove('/tmp/relations.tmp')

    # Verify that numeric, boolean, and null types are properly handled
    def test08_property_types(self):
        graphname = "tmpgraph4"
        # Write temporary files
        with open('/tmp/nodes.tmp', mode='w') as csv_file:
            out = csv.writer(csv_file)
            out.writerow(["numeric", "mixed", "bool"])
            out.writerow([0, '', True])
            out.writerow([5, "notnull", False])
            out.writerow([7, '', False]) # reused identifier
        with open('/tmp/relations.tmp', mode='w') as csv_file:
            out = csv.writer(csv_file)
            out.writerow(["src", "dest", "prop"])
            out.writerow([0, 5, True])
            out.writerow([5, 7, 3.5])
            out.writerow([7, 0, ''])

        runner = CliRunner()
        res = runner.invoke(bulk_insert, ['--port', port,
                                          '--nodes', '/tmp/nodes.tmp',
                                          '--relations', '/tmp/relations.tmp',
                                          graphname])

        self.env.assertEquals(res.exit_code, 0)
        self.env.assertIn('3 nodes created', res.output)
        self.env.assertIn('3 relations created', res.output)

        graph = Graph(graphname, redis_con)
        query_result = graph.query('MATCH (a)-[e]->() RETURN a.numeric, a.mixed, a.bool, e.prop ORDER BY a.numeric, e.prop')
        expected_result = [[0, None, True, True],
                           [5, 'notnull', False, 3.5],
                           [7, None, False, None]]

        # The graph should have the correct types for all properties
        self.env.assertEquals(query_result.result_set, expected_result)

    # Verify that the bulk loader does not block the server
    def test09_large_bulk_insert(self):
        graphname = "tmpgraph5"
        prop_str = "Property value to be repeated 1 million generating a multi-megabyte CSV"

        # Write temporary files
        filename = '/tmp/nodes.tmp'
        with open(filename, mode='w') as csv_file:
            out = csv.writer(csv_file)
            out.writerow(["long_property_string"])
            for i in range(100_000):
                out.writerow([prop_str])

        # Instantiate a thread to run the bulk loader
        thread = threading.Thread(target=run_bulk_loader, args=(graphname, filename))
        thread.start()

        # Ping server while bulk-loader is running
        ping_count = 0
        while thread.is_alive():
            t0 = time.time()
            redis_con.ping()
            t1 = time.time() - t0
            # Verify that pinging the server takes less than 1 second during bulk insertion
            self.env.assertLess(t1, 2)
            ping_count += 1

        thread.join()
        # Verify that at least one ping was issued
        self.env.assertGreater(ping_count, 1)
