"""Semantic work units must come from graph nodes and preserve boundaries."""

from contextlib import closing
import sqlite3
import sys
import unittest

from test_acceptance import SCRIPTS, fixture, git, invoke, test_directory

sys.path.insert(0, str(SCRIPTS))
import graph_store
from scan_files import inventory, snapshot_reader


class SemanticPlanner(unittest.TestCase):
    def planner(self):
        try:
            from semantic_planner import plan_from_graph
        except ModuleNotFoundError:
            self.fail('graph-based semantic work planner is not implemented')
        return plan_from_graph

    def test_snapshot_nodes_assignment_overlap_and_boundaries(self):
        with test_directory() as repo:
            revision = fixture(repo, {
                'src/api/main.ts': 'import { service } from "../service/logic.js";\nexport const entry = service;\n',
                'src/service/logic.ts': 'export function service() { return 1; }\n',
                'tests/api/main.test.ts': 'import { service } from "../../src/service/logic.js";\n',
                'docs/guide.md': '# Guide\n',
                'package.json': '{"bin":{"app":"src/api/main.ts"}}\n',
            })
            invoke(repo, 'map', '--commit', revision)
            manifest = inventory(repo, revision)
            with graph_store.database(repo / '.project-mapper/graph.sqlite') as db:
                plan, report = self.planner()(db, manifest)
                again = self.planner()(db, manifest)
                self.assertEqual((plan, report), again)
                self.assertEqual(plan['snapshot'], manifest['snapshot']['identity'])
                self.assertTrue(plan['questions'])
                node_keys = {key for key, in db.execute('SELECT key FROM nodes')}
                assigned = {node for task in plan['questions'] for node in task['node_ids']}
                self.assertTrue(assigned <= node_keys)
                self.assertIn('file:src/api/main.ts', assigned)
                self.assertIn('file:tests/api/main.test.ts', assigned)
                self.assertIn('file:docs/guide.md', assigned)
                self.assertTrue(any(unit['frontier_count'] for unit in report['units']))
                self.assertTrue(any(task['seeds'] == ['tests/api/main.test.ts']
                                    for task in plan['questions']))
                for task in plan['questions']:
                    self.assertTrue(task['node_ids'])
                    self.assertTrue(task['seeds'])
                    self.assertTrue(all(p in {e['path'] for e in manifest['entries'] if e['eligible']}
                                        for p in task['seeds']))

    def test_node_without_source_is_unassigned_and_snapshot_mismatch_rejected(self):
        with test_directory() as repo:
            revision = fixture(repo, {'package.json': '{"name":"demo"}\n'})
            invoke(repo, 'map', '--commit', revision)
            manifest = inventory(repo, revision)
            path = repo / '.project-mapper/graph.sqlite'
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("INSERT INTO nodes VALUES ('orphan:x','symbol','example','x',0)")
            with graph_store.database(path) as db:
                _, report = self.planner()(db, manifest)
                self.assertTrue(any(row['node'] == 'orphan:x' for row in report['unassigned']))
                mismatch = dict(manifest, snapshot=dict(manifest['snapshot'], identity='wrong'))
                with self.assertRaises(Exception):
                    self.planner()(db, mismatch)

    def test_number_of_units_is_not_globally_capped(self):
        with test_directory() as repo:
            files = {f'module_{i}/main.js': 'export const value = 1;\n' for i in range(8)}
            revision = fixture(repo, files)
            invoke(repo, 'map', '--commit', revision)
            with graph_store.database(repo / '.project-mapper/graph.sqlite') as db:
                plan, _ = self.planner()(db, inventory(repo, revision))
                self.assertGreaterEqual(len(plan['questions']), 8)

    def test_shared_configuration_is_attributed_to_production_and_tests(self):
        with test_directory() as repo:
            revision = fixture(repo, {
                'src/api/main.ts': 'const x = process.env.SHARED_SETTING;\n',
                'tests/api/main.test.ts': 'const y = process.env.SHARED_SETTING;\n',
            })
            invoke(repo, 'map', '--commit', revision)
            with graph_store.database(repo / '.project-mapper/graph.sqlite') as db:
                plan, report = self.planner()(db, inventory(repo, revision))
                tasks = [task for task in plan['questions'] if 'config:SHARED_SETTING' in task['node_ids']]
                self.assertEqual(len(tasks), 2)
                self.assertEqual({task['seeds'][0] for task in tasks},
                                 {'src/api/main.ts', 'tests/api/main.test.ts'})
                self.assertEqual(report['counts']['assigned_multiple'], 1)
                self.assertEqual(report['counts']['nodes'], report['counts']['assigned'] +
                                 report['counts']['unassigned'])

    def test_large_file_is_split_and_each_unit_retains_file_anchor(self):
        with test_directory() as repo:
            source = ''.join(f'export const symbol_{i} = {i};\n' for i in range(350))
            revision = fixture(repo, {'src/many.ts': source})
            invoke(repo, 'map', '--commit', revision)
            with graph_store.database(repo / '.project-mapper/graph.sqlite') as db:
                plan, report = self.planner()(db, inventory(repo, revision))
                tasks = [task for task in plan['questions'] if 'src/many.ts' in task['seeds']]
                self.assertGreater(len(tasks), 1)
                self.assertTrue(all('file:src/many.ts' in task['node_ids'] for task in tasks))
                self.assertTrue(all(len(task['node_ids']) <= report['limits']['nodes_per_unit']
                                    for task in tasks))
                assigned = {node for task in tasks for node in task['node_ids']}
                for node, in db.execute("SELECT key FROM nodes WHERE kind='symbol'"):
                    self.assertIn(node, assigned)
                self.assertFalse(report['unmapped_paths'])

    def test_cross_area_import_is_recorded_as_a_frontier_not_a_call(self):
        with test_directory() as repo:
            revision = fixture(repo, {
                'src/server/bindings.ts': 'import { handle } from "../application/handler.js";\n'
                                          'export const tools = { handle_request: { run: () => handle() } };\n',
                'src/application/handler.ts': 'export function handle() { return 1; }\n',
            })
            invoke(repo, 'map', '--commit', revision)
            with graph_store.database(repo / '.project-mapper/graph.sqlite') as db:
                plan, report = self.planner()(db, inventory(repo, revision))
                task = next(t for t in plan['questions'] if
                            'tool-candidate:src/server/bindings.ts:handle_request' in t['node_ids'])
                unit = next(u for u in report['units'] if u['id'] == task['id'])
                edge = next(e for e in unit['frontier_preview']
                            if e['source'] == 'file:src/server/bindings.ts'
                            and e['target'] == 'file:src/application/handler.ts')
                self.assertEqual(edge['type'], 'imports')
                self.assertEqual(unit['area_basis'], 'directory scheduling bucket')

    def test_submodule_boundary_is_visible_and_not_a_readable_seed(self):
        with test_directory() as repo:
            revision = fixture(repo, {'src/main.ts': 'export const value = 1;\n'})
            git(repo, 'update-index', '--add', '--cacheinfo', f'160000,{revision},third_party/library')
            git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test',
                '-c', 'commit.gpgsign=false', 'commit', '-qm', 'add gitlink')
            revision = git(repo, 'rev-parse', 'HEAD').decode().strip()
            invoke(repo, 'map', '--commit', revision)
            with graph_store.database(repo / '.project-mapper/graph.sqlite') as db:
                plan, report = self.planner()(db, inventory(repo, revision))
                self.assertTrue(any(item['path'] == 'third_party/library' and item['kind'] == 'submodule'
                                    for item in report['inventory_boundaries']))
                self.assertTrue(any(item['node'] == 'boundary:third_party/library' and
                                    item['status'] == 'boundary' for item in report['unassigned']))
                self.assertTrue(all('third_party/library' not in task['seeds'] for task in plan['questions']))

    def test_nonprintable_identifiers_remain_pending_and_do_not_invalidate_plan(self):
        with test_directory() as repo:
            odd_path = 'src/odd\u0085name.ts'
            revision = fixture(repo, {odd_path: 'export const value = 1;\n',
                                      'src/okay.ts': 'export const ready = 1;\n'})
            invoke(repo, 'map', '--commit', revision)
            manifest = inventory(repo, revision)
            with graph_store.database(repo / '.project-mapper/graph.sqlite') as db:
                plan, report = self.planner()(db, manifest)
                self.assertTrue(any(item['node'] == 'file:' + odd_path and item['status'] == 'pending'
                                    for item in report['unassigned']))
                self.assertIn(odd_path, report['unmapped_paths'])
                self.assertTrue(all(all(node.isprintable() and node == node.strip() for node in task['node_ids'])
                                    for task in plan['questions']))
                self.assertTrue(all(all(path.isprintable() and path == path.strip() for path in task['seeds'])
                                    for task in plan['questions']))

    def test_binary_is_not_given_to_a_text_worker_and_unknown_formats_are_not_discarded(self):
        with test_directory() as repo:
            fixture(repo, {'assets/logo.png': 'initial', 'docs/guide.md': '# Guide\n',
                           'src/binary.js': 'initial',
                           'src/Bridge.java': 'class Bridge {}\n',
                           'tools/latin.py': '# coding: latin-1\n# olé\n'})
            (repo / 'assets/logo.png').write_bytes(b'\xff\x00\x89PNG')
            (repo / 'src/binary.js').write_bytes(b'export const x = 1;\x00hidden')
            (repo / 'tools/latin.py').write_bytes('# coding: latin-1\n# olé\n'.encode('latin-1'))
            git(repo, 'add', '-f', '.')
            git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test',
                '-c', 'commit.gpgsign=false', 'commit', '-qm', 'binary and encoded Python')
            revision = git(repo, 'rev-parse', 'HEAD').decode().strip()
            invoke(repo, 'map', '--commit', revision)
            manifest = inventory(repo, revision)
            with graph_store.database(repo / '.project-mapper/graph.sqlite') as db:
                with snapshot_reader(repo, manifest) as reader:
                    plan, report = self.planner()(db, manifest, reader)
                seeds = {seed for task in plan['questions'] for seed in task['seeds']}
                self.assertNotIn('assets/logo.png', seeds)
                self.assertNotIn('src/binary.js', seeds)
                self.assertTrue({'docs/guide.md', 'src/Bridge.java', 'tools/latin.py'} <= seeds)
                self.assertTrue(any(item['path'] == 'assets/logo.png' and item['status'] == 'boundary'
                                    for item in report['unreadable_paths']))
                self.assertTrue(any(item['path'] == 'src/binary.js' and item['status'] == 'boundary'
                                    for item in report['unreadable_paths']))
                self.assertIn('assets/logo.png', report['unmapped_paths'])


if __name__ == '__main__':
    unittest.main()
