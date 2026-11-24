from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import os
import sqlite3
import subprocess
import sys
import unittest

from test_acceptance import fixture, git, invoke, test_directory
from test_investigation import accept, add_question, publish_investigation, save


class MultidimensionalCLI(unittest.TestCase):
    def test_offline_queries_need_no_git_and_identify_unverified_snapshot(self):
        with test_directory() as repo:
            revision = fixture(repo, {'package.json': '{"name":"demo"}\n'})
            invoke(repo, 'map', '--commit', revision)
            cli = Path(__file__).resolve().parents[1] / 'scripts/project_mapper.py'
            env = dict(os.environ, PATH='')

            def query(*args):
                return subprocess.run([sys.executable, str(cli), str(repo), '--offline', *args],
                                      capture_output=True, text=True, env=env)

            search = query('search', 'package.json')
            self.assertEqual(search.returncode, 0, search.stderr)
            found = json.loads(search.stdout)
            self.assertEqual(found['graph_identity']['snapshot']['revision'], revision)
            self.assertFalse(found['graph_identity']['current_snapshot_verified'])
            self.assertTrue(any(n['key'] == 'file:package.json' for n in found['nodes']))
            node = query('node', 'file:package.json')
            self.assertEqual(node.returncode, 0, node.stderr)
            self.assertEqual(json.loads(node.stdout)['graph_identity']['sha256'],
                             found['graph_identity']['sha256'])
            self.assertEqual(query('trace', 'file:package.json', '--depth', '1').returncode, 0)
            self.assertEqual(query('coverage', '--summary').returncode, 0)
            self.assertNotEqual(query('verify').returncode, 0)
            self.assertNotEqual(query('node', 'file:package.json', '--run', 'invalid').returncode, 0)

    def test_expected_revision_rejects_stale_commits_and_worktree_maps(self):
        with test_directory() as repo:
            revision = fixture(repo, {'package.json': '{"name":"demo"}\n'})
            invoke(repo, 'map', '--commit', revision)
            (repo / 'package.json').write_text('{"name":"updated"}\n', encoding='utf-8')
            git(repo, 'add', 'package.json')
            git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test',
                '-c', 'commit.gpgsign=false', 'commit', '-qm', 'advance')
            head = git(repo, 'rev-parse', 'HEAD').decode().strip()
            self.assertEqual(invoke(repo, 'verify')['snapshot']['revision'], revision)
            for mode, command in (((), ('verify',)), (('--offline',), ('search', 'package.json'))):
                with self.subTest(command=command):
                    stale = invoke(repo, *mode, '--expect-revision', head, *command, ok=False)
                    self.assertNotEqual(stale.returncode, 0)
                    self.assertIn('differs from expected revision', stale.stderr)
                    self.assertEqual(stale.stdout, '')
                    self.assertEqual(invoke(repo, *mode, '--expect-revision', revision, *command)
                                     ['snapshot']['revision'], revision)
            invalid = invoke(repo, '--expect-revision', 'HEAD', 'verify', ok=False)
            self.assertIn('requires a full Git commit hash', invalid.stderr)
            invoke(repo, 'map', '--worktree')
            worktree = invoke(repo, '--expect-revision', head, 'verify', ok=False)
            self.assertIn('found a worktree snapshot', worktree.stderr)

    def test_map_and_enrichment_replay_the_same_snapshot(self):
        with test_directory() as repo:
            revision = fixture(repo, {
                'package.json': '{"bin":{"rea":"scripts/rea.mjs"}}\n',
                'scripts/rea.mjs': 'import "../src/main.js";\n',
                'src/main.ts': 'export const name = "rea";\n',
            })
            mapped = invoke(repo, 'map', '--commit', revision)
            self.assertGreater(mapped['nodes'], 0)
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')
            structural = invoke(repo, 'search', 'package.json')['nodes']
            self.assertTrue(any(row['key'] == 'file:package.json' for row in structural))
            summary = invoke(repo, 'coverage', '--summary')
            self.assertTrue(any(row['family'] == 'multidimensional-static' for row in summary['summary']))
            self.assertNotIn('coverage', summary)
            dimensions = invoke(repo, 'dimensions', '--summary')['dimensions']
            self.assertTrue(any(row['dimension'] == 'entrypoint' for row in dimensions))
            trace = invoke(repo, 'trace', 'file:scripts/rea.mjs')
            self.assertTrue(trace['analysis_incomplete'])
            self.assertTrue(any(row['family'] == 'multidimensional-static' for row in trace['coverage_frontier']))
            compact = invoke(repo, 'trace', 'file:scripts/rea.mjs', '--summary')
            self.assertEqual(Counter({(row['family'], row['status']): row['count']
                                      for row in compact.pop('coverage_frontier_summary')}),
                             Counter((row['family'], row['status']) for row in trace.pop('coverage_frontier')))
            self.assertEqual(compact, trace)

            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'start', 'Where is the entry declared?', ['package.json'])
            page = invoke(repo, 'read-input', run['run'], 'start', 'package.json', '--count', '1')
            anchor = dict(path='package.json', content_id=page['content_id'], start=1, end=1)
            shard = dict(snapshot=run['snapshot']['identity'], question='start', status='answered', gap='',
                         claims=[dict(source='file:package.json', relation='describes',
                                      target='command:rea', condition='', evidence=[anchor])])
            save(Path(run['shards']) / 'start.json', shard)
            accept(repo, run, 'start')
            publish_investigation(repo, run)
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')
            node = invoke(repo, 'node', 'file:package.json')['nodes'][0]
            self.assertTrue(any(edge['type'] == 'describes' for edge in node['outgoing']))
            self.assertTrue(invoke(repo, 'search', 'package.json')['nodes'])

            # Replacing the richer map with a static-only map must fail closed.
            attempt = invoke(repo, 'map', '--commit', revision, ok=False)
            self.assertNotEqual(attempt.returncode, 0)
            self.assertIn('active investigation preserved', attempt.stderr)
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')
            with closing(sqlite3.connect(repo / '.project-mapper/graph.sqlite')) as database, database:
                database.execute("UPDATE nodes SET name='tampered' WHERE key='file:package.json'")
            self.assertNotEqual(invoke(repo, 'verify', ok=False).returncode, 0)

    def test_missing_profile_marker_cannot_discard_the_static_map(self):
        with test_directory() as repo:
            revision = fixture(repo, {'package.json': '{"name":"demo"}\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'name', 'What is the package name?', ['package.json'])
            page = invoke(repo, 'read-input', run['run'], 'name', 'package.json', '--count', '1')
            anchor = dict(path='package.json', content_id=page['content_id'], start=1, end=1)
            save(Path(run['shards']) / 'name.json', dict(snapshot=run['snapshot']['identity'],
                 question='name', status='answered', gap='', claims=[dict(source='file:package.json',
                 relation='declares', target='package:demo', condition='', evidence=[anchor])]))
            accept(repo, run, 'name')
            (Path(run['plan']).parent / 'static-profile.json').unlink()
            attempt = publish_investigation(repo, run, ok=False)
            self.assertNotEqual(attempt.returncode, 0)
            self.assertIn('active multidimensional map preserved', attempt.stderr)
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

    def test_changed_worktree_invalidates_map(self):
        with test_directory() as repo:
            fixture(repo, {'package.json': '{"name":"demo"}\n'})
            invoke(repo, 'map', '--worktree')
            (repo / 'package.json').write_text('{"name":"changed"}\n', encoding='utf-8')
            self.assertNotEqual(invoke(repo, 'verify', ok=False).returncode, 0)

    def test_python_profile_is_included_and_replayed(self):
        with test_directory() as repo:
            revision = fixture(repo, {'bridge.py': 'def start():\n    return 1\n',
                                      'package.json': '{"name":"demo"}\n'})
            invoke(repo, 'map', '--commit', revision)
            nodes = invoke(repo, 'node', 'function:bridge:start')['nodes']
            self.assertEqual(nodes[0]['name'], 'start')
            coverage = invoke(repo, 'coverage', '--family', 'python-static')['coverage']
            self.assertTrue(any(row['area'] == 'bridge.py' and row['findings'] > 0 for row in coverage))
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

    def test_investigation_can_reference_an_indexed_symbol_by_exact_id(self):
        with test_directory() as repo:
            revision = fixture(repo, {'src/main.ts': 'export const run = () => 1;\n'})
            invoke(repo, 'map', '--commit', revision)
            symbol = 'symbol:src/main.ts:run'
            self.assertEqual(invoke(repo, 'node', symbol)['nodes'][0]['name'], 'run')
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'behavior', 'What is the returned value?', ['src/main.ts'])
            page = invoke(repo, 'read-input', run['run'], 'behavior', 'src/main.ts', '--count', '1')
            anchor = dict(path='src/main.ts', content_id=page['content_id'], start=1, end=1)
            save(Path(run['shards']) / 'behavior.json', dict(snapshot=run['snapshot']['identity'],
                 question='behavior', status='answered', gap='', claims=[dict(source=symbol,
                 relation='returns', target='value:one', condition='', evidence=[anchor])]))
            accept(repo, run, 'behavior')
            publish_investigation(repo, run)
            node = invoke(repo, 'node', symbol)['nodes'][0]
            self.assertEqual(node['name'], 'run')
            self.assertTrue(any(edge['type'] == 'returns' for edge in node['outgoing']))
            self.assertEqual({item['basis'] for item in node['evidence']},
                             {'javascript-lexical-export', 'agent-source-reading'})
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

    def test_investigation_reconciles_configuration_and_npm_script_ids(self):
        with test_directory() as repo:
            revision = fixture(repo, {
                'src/main.ts': 'const limit = process.env.REA_ASAR_MAX_LISTING_BYTES;\n',
                'package.json': '{"scripts":{"build":"node build.js"}}\n',
            })
            invoke(repo, 'map', '--commit', revision)
            config = 'config:REA_ASAR_MAX_LISTING_BYTES'
            script = 'npm-script:package.json:build'
            self.assertEqual(invoke(repo, 'node', config)['nodes'][0]['kind'], 'configuration')
            self.assertEqual(invoke(repo, 'node', script)['nodes'][0]['kind'], 'command')
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'config', 'Which setting is read?', ['src/main.ts', 'package.json'])
            page = invoke(repo, 'read-input', run['run'], 'config', 'src/main.ts', '--count', '1')
            anchor = dict(path='src/main.ts', content_id=page['content_id'], start=1, end=1)
            claims = [dict(source='file:src/main.ts', relation='reads', target=config,
                           condition='', evidence=[anchor]),
                      dict(source=script, relation='related-to', target=config,
                           condition='', evidence=[anchor])]
            save(Path(run['shards']) / 'config.json', dict(snapshot=run['snapshot']['identity'],
                 question='config', status='answered', gap='', claims=claims))
            accept(repo, run, 'config')
            publish_investigation(repo, run)
            node = invoke(repo, 'node', config)['nodes'][0]
            self.assertEqual((node['kind'], node['name']), ('configuration', 'REA_ASAR_MAX_LISTING_BYTES'))
            self.assertEqual({item['authority'] for item in node['evidence']}, {'candidate', 'source'})
            self.assertEqual(invoke(repo, 'node', script)['nodes'][0]['kind'], 'command')
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

    def test_new_run_cannot_replace_prior_investigation_findings(self):
        with test_directory() as repo:
            revision = fixture(repo, {'src/main.ts': 'export const run = () => 1;\n'})
            invoke(repo, 'map', '--commit', revision)
            for index in (1, 2):
                run = invoke(repo, 'investigate', '--commit', revision)
                question = f'question{index}'
                add_question(run, question, 'What is the behavior?', ['src/main.ts'])
                page = invoke(repo, 'read-input', run['run'], question, 'src/main.ts', '--count', '1')
                anchor = dict(path='src/main.ts', content_id=page['content_id'], start=1, end=1)
                save(Path(run['shards']) / f'{question}.json', dict(snapshot=run['snapshot']['identity'],
                     question=question, status='answered', gap='', claims=[dict(source='file:src/main.ts',
                     relation=f'claim{index}', target=f'value:{index}', condition='', evidence=[anchor])]))
                accept(repo, run, question)
                if index == 1:
                    publish_investigation(repo, run)
                else:
                    attempt = publish_investigation(repo, run, ok=False)
                    self.assertNotEqual(attempt.returncode, 0)
                    self.assertIn('omits or changes accepted findings', attempt.stderr)
            node = invoke(repo, 'node', 'file:src/main.ts')['nodes'][0]
            self.assertTrue(any(edge['type'] == 'claim1' for edge in node['outgoing']))
            self.assertFalse(any(edge['type'] == 'claim2' for edge in node['outgoing']))
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

    def test_same_run_can_revise_accepted_finding(self):
        with test_directory() as repo:
            revision = fixture(repo, {'src/main.ts': 'export const run = () => 1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'behavior', 'What is the behavior?', ['src/main.ts'])
            page = invoke(repo, 'read-input', run['run'], 'behavior', 'src/main.ts', '--count', '1')
            anchor = dict(path='src/main.ts', content_id=page['content_id'], start=1, end=1)
            shard_path = Path(run['shards']) / 'behavior.json'
            for target in ('value:old', 'value:corrected'):
                save(shard_path, dict(snapshot=run['snapshot']['identity'], question='behavior',
                     status='answered', gap='', claims=[dict(source='file:src/main.ts',
                     relation='returns', target=target, condition='', evidence=[anchor])]))
                accept(repo, run, 'behavior')
                publish_investigation(repo, run)
            node = invoke(repo, 'node', 'file:src/main.ts')['nodes'][0]
            targets = {edge['target'] for edge in node['outgoing'] if edge['type'] == 'returns'}
            self.assertEqual(targets, {'value:corrected'})
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')


if __name__ == '__main__':
    unittest.main()
