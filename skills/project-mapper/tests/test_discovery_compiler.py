from contextlib import closing
import json
import sqlite3
import unittest

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, load, publish_investigation, save, write_answer


class DiscoveryCompiler(unittest.TestCase):
    def setUp(self):
        self.repo = self.enterContext(test_directory())
        revision = fixture(self.repo, {'rules.json': '{"original": null}\n{"drop": false}\n'})
        self.run = invoke(self.repo, 'investigate', '--commit', revision)
        entry = next(row for row in load(self.run['inventory'])['entries'] if row['path'] == 'rules.json')
        self.locator = dict(path=entry['path'], content_id=entry['content_id'], start=1, end=1)
        self.graph = self.repo / '.project-mapper/graph.sqlite'
        for key in ('read', 'drop'):
            add_question(self.run, key, 'What happens for ' + key + '?', ['rules.json'])

    def shard(self, question, discoveries, claims=()):
        path = write_answer(self.run, question, list(claims))
        save(path, dict(load(path), discoveries=discoveries))
        return path

    def discovery(self, key, content, pointer=''):
        return dict(id=key, title='Retention', summary='Local retention policy.', terms=['release'],
                    content=content, support=[dict(pointer=pointer, evidence=[self.locator])])

    def test_forward_reference_and_pointer_support_round_trip(self):
        claim = dict(source='b', target='a', relation='member-of', condition='same revision', evidence=[self.locator])
        first = self.discovery('a', {'~/':['ignored', False]}, '/~0~1/1')
        second = self.discovery('b', None)
        self.shard('read', [first], [claim])
        accept(self.repo, self.run, 'read')
        self.shard('drop', [second])
        accept(self.repo, self.run, 'drop')
        publish_investigation(self.repo, self.run)
        self.assertEqual(invoke(self.repo, 'verify')['integrity'], 'ok')
        with closing(sqlite3.connect(self.graph)) as db:
            self.assertEqual([(row[0], json.loads(row[4])) for row in db.execute('select * from discoveries order by 1')],
                             [('a', first['content']), ('b', None)])
            self.assertEqual(list(db.execute('select node,pointer from discovery_support order by 1')),
                             [('a', '/~0~1/1'), ('b', '')])
        self.assertEqual(invoke(self.repo, 'dimensions')['memberships'][0]['group_key'], 'a')
        self.assertEqual(invoke(self.repo, 'coverage')['investigation_scope']['answered'], 2)
        original = self.graph.read_bytes()
        for replacement, error in [([self.discovery('a', None)], 'duplicate discovery id'),
                                   ([self.discovery('different', None)], 'endpoint')]:
            self.shard('drop', replacement)
            accept(self.repo, self.run, 'drop')
            failed = publish_investigation(self.repo, self.run, ok=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn(error, failed.stderr)
            self.assertEqual(self.graph.read_bytes(), original)

    def test_discovery_keys_are_bounded_and_cannot_redefine_legacy_endpoints(self):
        for key in ('file:rules.json', 'service:api', 'x' * 257):
            with self.subTest(key=key):
                self.shard('read', [self.discovery(key, 'A finding')])
                result = invoke(self.repo, 'check-shard', self.run['run'], 'read', ok=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('discovery id', result.stderr)
        self.shard('read', [self.discovery('x' * 256, None)])
        self.assertEqual(accept(self.repo, self.run, 'read')['discoveries'], 1)

    def test_invalid_pointer_or_unsupported_value_rejected_at_review(self):
        for value, pointer in [({'x':[1]}, '/x/01'), ({'x':[1]}, '/x/-'), ({'~2':None}, '/~2'),
                               (False, '/missing'), ({'x':1}, 'x'), (float('inf'), '')]:
            with self.subTest(value=value, pointer=pointer):
                self.shard('read', [self.discovery('x', value, pointer)])
                result = invoke(self.repo, 'check-shard', self.run['run'], 'read', ok=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('Traceback', result.stderr)
                self.assertRegex(result.stderr, 'pointer|finite')
