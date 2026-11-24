"""CLI contract for graph-derived semantic assignments."""

import json
import argparse
from contextlib import ExitStack, closing, contextmanager
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import unittest
from unittest.mock import patch

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, publish_investigation, save

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import project_mapper as mapper


class GraphInvestigationContract(unittest.TestCase):
    def test_graph_swap_after_connect_never_returns_old_rows_as_new_generation(self):
        for command in ('graph-unit', 'node', 'trace', 'assignments', 'planning'):
            with self.subTest(command=command), test_directory() as repo:
                revision = fixture(repo, {'app.js': 'export const app=1;\n'})
                invoke(repo, 'map', '--commit', revision)
                run = invoke(repo, 'investigate', '--from-graph', '--commit', revision)
                plan = json.loads(Path(run['plan']).read_text(encoding='utf-8'))
                question = plan['questions'][0]
                graph = repo / '.project-mapper' / 'graph.sqlite'
                stage = Path(run['plan']).parent
                replacement = repo / '.project-mapper' / 'replacement.sqlite'
                shutil.copyfile(graph, replacement)
                with closing(sqlite3.connect(replacement)) as altered, altered:
                    altered.execute("UPDATE nodes SET name='new-generation' WHERE key='file:app.js'")
                original_database = mapper.store.database

                @contextmanager
                def swapped_database(path):
                    with ExitStack() as stack:
                        if os.name == 'nt':
                            # Keep the old view while releasing Windows' lock on the file being replaced.
                            old_connection = stack.enter_context(closing(sqlite3.connect(':memory:')))
                            old_connection.row_factory = sqlite3.Row
                            with original_database(path) as published:
                                published.backup(old_connection)
                        else:
                            old_connection = stack.enter_context(original_database(path))
                        old_connection.execute('SELECT count(*) FROM nodes').fetchone()
                        os.replace(replacement, graph)
                        new_pin = mapper.graph_fingerprint(graph)
                        mapper.save_graph_pin(stage, dict(snapshot=plan['snapshot'], **new_pin))
                        yield old_connection

                unit = argparse.Namespace(command='graph-unit', run=run['run'], question=question['id'],
                                          summary=True, node_offset=0, node_limit=25,
                                          edge_offset=0, limit=10, expect_graph=None)
                node = argparse.Namespace(command='node', run=run['run'], selector=question['node_ids'][0])
                trace = argparse.Namespace(command='trace', run=run['run'], selector=question['node_ids'][0],
                                           direction='out', type=[], depth=1, max_nodes=10, max_edges=10)
                with patch.object(mapper.store, 'database', side_effect=swapped_database):
                    with self.assertRaisesRegex(mapper.MappingError, 'graph changed'):
                        if command == 'assignments':
                            mapper.check_run_assignments(repo, json.loads(Path(run['inventory']).read_text()),
                                                         [question], stage=stage)
                        elif command == 'planning':
                            mapper.start_run(repo, revision, investigation=True, from_graph=True)
                        else:
                            mapper.dispatch(repo, {'graph-unit': unit, 'node': node, 'trace': trace}[command])

    def test_graph_assignments_use_matching_snapshot_and_pinned_queries(self):
        with test_directory() as repo:
            revision = fixture(repo, {'package.json': '{"bin":{"app":"app.js"}}\n',
                                      'app.js': 'export function main() { return 1; }\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--from-graph', '--commit', revision)
            plan = json.loads(Path(run['plan']).read_text(encoding='utf-8'))
            self.assertTrue(plan['questions'])
            self.assertEqual(plan['snapshot'], run['snapshot']['identity'])
            question = next(item for item in plan['questions'] if item['node_ids'])
            self.assertTrue(question['seeds'])
            prompt = invoke(repo, 'worker-prompt', run['run'], question['id'])['prompt']
            self.assertIn(question['node_ids'][0], prompt)
            self.assertIn('trace', prompt)
            self.assertEqual(invoke(repo, 'node', question['node_ids'][0], '--run', run['run'])
                             ['snapshot']['identity'], run['snapshot']['identity'])
            self.assertEqual(invoke(repo, 'trace', question['node_ids'][0], '--run', run['run'])
                             ['snapshot']['identity'], run['snapshot']['identity'])
            unit = invoke(repo, 'graph-unit', run['run'], question['id'], '--limit', '1')
            self.assertEqual(unit['question']['node_count'], len(question['node_ids']))
            self.assertEqual([node['key'] for node in unit['nodes']], question['node_ids'][:25])
            self.assertLessEqual(len(unit['edges']), 1)
            self.assertIn('truncated', unit)
            compact = invoke(repo, 'graph-unit', run['run'], question['id'], '--summary')
            self.assertNotIn('nodes', compact)
            self.assertNotIn('node_ids', compact['question'])
            self.assertEqual(compact['question_fingerprint'], unit['question_fingerprint'])

            question['node_ids'].append('file:does-not-exist')
            save(run['plan'], plan)
            failed = invoke(repo, 'check-plan', run['run'], ok=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('node', failed.stderr.lower())

    def test_graph_plan_requires_published_map_with_same_snapshot(self):
        with test_directory() as repo:
            revision = fixture(repo, {'a.js': 'export const a=1;\n'})
            failed = invoke(repo, 'investigate', '--from-graph', '--commit', revision, ok=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('graph', failed.stderr.lower())

            # Legacy hand-authored investigations remain possible with no map.
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'a', 'What does a declare?', ['a.js'])
            self.assertIn('questions', invoke(repo, 'check-plan', run['run'])['plan'])

    def test_batch_dispatch_and_plan_progress_are_bounded(self):
        with test_directory() as repo:
            revision = fixture(repo, {'src/main.js': 'export const main=1;\n',
                                      'tests/main.test.js': 'import "../src/main.js";\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--from-graph', '--commit', revision)
            page = invoke(repo, 'check-plan', run['run'], '--list', '--limit', '1')
            self.assertEqual(len(page['questions']), 1)
            self.assertEqual(page['questions'][0]['progress'], 'unexamined')
            self.assertIsNotNone(page['next_offset'])
            summary = invoke(repo, 'check-plan', run['run'], '--summary')
            self.assertLess(len(json.dumps(summary)), 2500)
            self.assertEqual(summary['progress']['unexamined'], summary['questions'])
            plan = json.loads(Path(run['plan']).read_text(encoding='utf-8'))
            first, second = plan['questions'][:2]
            batch = invoke(repo, 'worker-prompt', run['run'], first['id'], '--also', second['id'])['prompt']
            self.assertIn('Batch contract', batch)
            self.assertIn(first['id'], batch)
            self.assertIn(second['id'], batch)
            self.assertNotIn(first['node_ids'][0], batch)
            duplicate = invoke(repo, 'worker-prompt', run['run'], first['id'], '--also', first['id'], ok=False)
            self.assertNotEqual(duplicate.returncode, 0)
            second['depends_on'] = [first['id']]
            save(run['plan'], plan)
            dependent = invoke(repo, 'worker-prompt', run['run'], first['id'], '--also', second['id'], ok=False)
            self.assertNotEqual(dependent.returncode, 0)

    def test_tampered_graph_is_rejected_before_planning(self):
        with test_directory() as repo:
            revision = fixture(repo, {'app.js': 'export const app=1;\n'})
            invoke(repo, 'map', '--commit', revision)
            graph = repo / '.project-mapper' / 'graph.sqlite'
            with closing(sqlite3.connect(graph)) as connection, connection:
                connection.execute("UPDATE nodes SET name='tampered' WHERE key='file:app.js'")
            failed = invoke(repo, 'investigate', '--from-graph', '--commit', revision, ok=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('do not reproduce', failed.stderr)

    def test_tampered_graph_is_rejected_before_publication(self):
        with test_directory() as repo:
            revision = fixture(repo, {'app.js': 'export const app=1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--from-graph', '--commit', revision)
            plan = json.loads(Path(run['plan']).read_text(encoding='utf-8'))
            question = plan['questions'][0]
            page = invoke(repo, 'read-input', run['run'], question['id'], 'app.js', '--count', '1')
            source = dict(path='app.js', content_id=page['content_id'], start=1, end=1)
            save(Path(run['shards']) / (question['id'] + '.json'),
                 dict(snapshot=plan['snapshot'], question=question['id'], status='answered', gap='',
                      claims=[dict(source='file:app.js', relation='describes', target='component:app',
                                   condition='', evidence=[source])]))
            accept(repo, run, question['id'])
            reviewed = invoke(repo, 'check-plan', run['run'])['fingerprint']
            graph = repo / '.project-mapper' / 'graph.sqlite'
            with closing(sqlite3.connect(graph)) as connection, connection:
                connection.execute("UPDATE nodes SET name='tampered' WHERE key='file:app.js'")
            rejected_plan = invoke(repo, 'check-plan', run['run'], ok=False)
            self.assertNotEqual(rejected_plan.returncode, 0)
            failed = invoke(repo, 'publish', run['run'], '--reviewed-english-plan', reviewed, ok=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('graph changed', failed.stderr)
            with closing(sqlite3.connect(graph)) as connection:
                self.assertEqual(connection.execute("SELECT name FROM nodes WHERE key='file:app.js'").fetchone()[0],
                                 'tampered')

    def test_injected_node_is_rejected_before_worker_receives_it(self):
        with test_directory() as repo:
            revision = fixture(repo, {'app.js': 'export const app=1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--from-graph', '--commit', revision)
            plan = json.loads(Path(run['plan']).read_text(encoding='utf-8'))
            question = plan['questions'][0]
            graph = repo / '.project-mapper' / 'graph.sqlite'
            with closing(sqlite3.connect(graph)) as connection, connection:
                connection.execute("INSERT INTO nodes VALUES ('symbol:app.js:phantom','symbol','app.js','phantom',0)")
            question['node_ids'].append('symbol:app.js:phantom')
            save(run['plan'], plan)
            for command in [('check-plan', run['run'], '--summary'),
                            ('worker-prompt', run['run'], question['id']),
                            ('graph-unit', run['run'], question['id'])]:
                failed = invoke(repo, *command, ok=False)
                self.assertNotEqual(failed.returncode, 0)
                self.assertIn('graph changed', failed.stderr)

    def test_windows_pin_hashes_even_if_recorded_stamp_is_unchanged(self):
        with test_directory() as repo:
            revision = fixture(repo, {'app.js': 'export const app=1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--from-graph', '--commit', revision)
            stage = Path(run['plan']).parent
            graph = repo / '.project-mapper' / 'graph.sqlite'
            with patch.object(mapper.os, 'name', 'nt'), \
                    patch.object(mapper, 'graph_fingerprint', wraps=mapper.graph_fingerprint) as fingerprint:
                mapper.check_graph_pin(stage, graph, run['snapshot']['identity'])
                self.assertEqual(fingerprint.call_count, 1)

    def test_progressive_publication_updates_graph_pin(self):
        with test_directory() as repo:
            revision = fixture(repo, {'app.js': 'export const app=1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--from-graph', '--commit', revision)
            plan = json.loads(Path(run['plan']).read_text(encoding='utf-8'))
            question = plan['questions'][0]
            generation = invoke(repo, 'graph-unit', run['run'], question['id'], '--summary')['graph_fingerprint']
            page = invoke(repo, 'read-input', run['run'], question['id'], 'app.js', '--count', '1')
            source = dict(path='app.js', content_id=page['content_id'], start=1, end=1)
            save(Path(run['shards']) / (question['id'] + '.json'),
                 dict(snapshot=plan['snapshot'], question=question['id'], status='answered', gap='',
                      claims=[dict(source='file:app.js', relation='describes', target='component:app',
                                   condition='', evidence=[source])]))
            accept(repo, run, question['id'])
            publish_investigation(repo, run)
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')
            latest = invoke(repo, 'graph-unit', run['run'], question['id'], '--summary')
            self.assertEqual(latest['question']['id'], question['id'])
            self.assertNotEqual(latest['graph_fingerprint'], generation)
            old_page = invoke(repo, 'graph-unit', run['run'], question['id'], '--expect-graph', generation, ok=False)
            self.assertNotEqual(old_page.returncode, 0)
            self.assertIn('generation changed', old_page.stderr)
            current = invoke(repo, 'graph-unit', run['run'], question['id'],
                             '--expect-graph', latest['graph_fingerprint'])
            self.assertEqual(current['graph_fingerprint'], latest['graph_fingerprint'])

    def test_publish_reuses_only_current_replayed_static_base(self):
        with test_directory() as repo:
            revision = fixture(repo, {'src/a.js': 'export const a=1;\n',
                                      'tests/b.js': 'export const b=2;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--from-graph', '--commit', revision)
            plan = json.loads(Path(run['plan']).read_text(encoding='utf-8'))
            for index, question in enumerate(plan['questions'][:2]):
                path = question['seeds'][0]
                page = invoke(repo, 'read-input', run['run'], question['id'], path, '--count', '1')
                ref = dict(path=path, content_id=page['content_id'], start=1, end=1)
                save(Path(run['shards']) / (question['id'] + '.json'),
                     dict(snapshot=plan['snapshot'], question=question['id'], status='answered', gap='',
                          claims=[dict(source='file:' + path, relation='describes',
                                       target='component:test-' + str(index), condition='', evidence=[ref])]))
                accept(repo, run, question['id'])
                reviewed = invoke(repo, 'check-plan', run['run'])['fingerprint']
                with patch.object(mapper, 'multidimensional_rows', wraps=mapper.multidimensional_rows) as extract:
                    mapper.publish(repo, run['run'], reviewed_english_plan=reviewed)
                    self.assertEqual(extract.call_count, 1)
                self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')
            self.assertTrue(invoke(repo, 'node', 'component:test-0')['nodes'])
            self.assertTrue(invoke(repo, 'node', 'component:test-1')['nodes'])

    def test_role_coverage_is_published_unconditional_and_deduplicated(self):
        with test_directory() as repo:
            revision = fixture(repo, {'src/a.js': 'export const a=1;\n',
                                      'tests/b.js': 'export const b=2;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--from-graph', '--commit', revision)
            plan = json.loads(Path(run['plan']).read_text(encoding='utf-8'))
            a, b = 'file:src/a.js', 'file:tests/b.js'
            first = next(q for q in plan['questions'] if a in q['node_ids'])
            second = next(q for q in plan['questions'] if b in q['node_ids'])
            self.assertNotEqual(first['id'], second['id'])
            second['node_ids'].append(a)  # Both assignments may share a node.
            save(run['plan'], plan)
            refs = {}
            for path in ('src/a.js', 'tests/b.js'):
                page = invoke(repo, 'read-input', run['run'], first['id'], path, '--count', '1')
                refs[path] = dict(path=path, content_id=page['content_id'], start=1, end=1)
            def discovery(key, node, ref):
                return dict(id=key, title=key, summary='A node role.', terms=[],
                            content={'subject_node': node, 'role': 'Exports a value.'},
                            support=[dict(pointer='/subject_node', evidence=[ref]),
                                     dict(pointer='/role', evidence=[ref])])
            discoveries = [discovery('a-role', a, refs['src/a.js']),
                           discovery('b-role', b, refs['tests/b.js'])]
            claims = [dict(source='a-role', relation='describes', target=a, condition='',
                           evidence=[refs['src/a.js']]),
                      dict(source='b-role', relation='describes', target=b, condition='when enabled',
                           evidence=[refs['tests/b.js']])]
            save(Path(run['shards']) / (first['id'] + '.json'),
                 dict(snapshot=plan['snapshot'], question=first['id'], status='partial',
                      gap='Not all assigned nodes were investigated.', discoveries=discoveries, claims=claims))
            accept(repo, run, first['id'])
            before = invoke(repo, 'check-plan', run['run'], '--summary')
            self.assertEqual(before['published_unconditional_node_roles'], 0)
            self.assertEqual(before['assigned_without_unconditional_role'], before['assigned_nodes'])
            publish_investigation(repo, run)
            after = invoke(repo, 'check-plan', run['run'], '--summary')
            self.assertEqual(after['published_unconditional_node_roles'], 1)
            self.assertEqual(after['assigned_without_unconditional_role'], after['assigned_nodes'] - 1)
            for question in (first, second):
                unit = invoke(repo, 'graph-unit', run['run'], question['id'], '--summary')
                self.assertEqual(unit['published_unconditional_node_roles'], 1)
                self.assertEqual(unit['assigned_without_unconditional_role'], len(question['node_ids']) - 1)
                self.assertIn('published', unit['role_coverage_basis'].lower())

    def test_changed_assigned_nodes_invalidate_prior_acceptance(self):
        with test_directory() as repo:
            revision = fixture(repo, {'src/app.js': 'export const app=1;\n',
                                      'src/other.js': 'export const other=2;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--from-graph', '--commit', revision)
            plan = json.loads(Path(run['plan']).read_text(encoding='utf-8'))
            question = plan['questions'][0]
            page = invoke(repo, 'read-input', run['run'], question['id'], 'src/app.js', '--count', '1')
            source = dict(path='src/app.js', content_id=page['content_id'], start=1, end=1)
            save(Path(run['shards']) / (question['id'] + '.json'),
                 dict(snapshot=plan['snapshot'], question=question['id'], status='answered', gap='',
                      claims=[dict(source='file:src/app.js', relation='describes', target='component:example',
                                   condition='', evidence=[source])]))
            accept(repo, run, question['id'])
            self.assertEqual(invoke(repo, 'check-plan', run['run'], '--question', question['id'])['progress'],
                             'accepted-answered')
            question['node_ids'].reverse()
            if len(question['node_ids']) < 2:
                question['node_ids'].append('file:src/other.js')
            save(run['plan'], plan)
            self.assertEqual(invoke(repo, 'check-plan', run['run'], '--question', question['id'])['progress'], 'stale')
            failed = publish_investigation(repo, run, ok=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('review', failed.stderr.lower())

    def test_run_queries_reject_changed_worktree(self):
        with test_directory() as repo:
            fixture(repo, {'app.js': 'export const app=1;\n'})
            invoke(repo, 'map', '--worktree')
            run = invoke(repo, 'investigate', '--from-graph', '--worktree')
            question = json.loads(Path(run['plan']).read_text(encoding='utf-8'))['questions'][0]
            (repo / 'app.js').write_text('export const app=2;\n', encoding='utf-8')
            for command in [('graph-unit', run['run'], question['id']),
                            ('node', question['node_ids'][0], '--run', run['run']),
                            ('trace', question['node_ids'][0], '--run', run['run'])]:
                failed = invoke(repo, *command, ok=False)
                self.assertNotEqual(failed.returncode, 0)
                self.assertIn('snapshot changed', failed.stderr)


if __name__ == '__main__':
    unittest.main()
