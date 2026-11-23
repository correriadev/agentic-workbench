"""Direct semantic context is discoverable from a structural node."""

from pathlib import Path
import unittest

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, publish_investigation, save


class NodeContext(unittest.TestCase):
    def test_node_exposes_direct_reviewed_context_in_both_directions(self):
        with test_directory() as repo:
            revision = fixture(repo, {'package.json': '{"bin":{"rea":"scripts/rea.mjs"}}\n',
                                      'scripts/rea.mjs': 'export const main = () => 1;\n',
                                      'other.js': 'export const unrelated = true;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'entry', 'What is the executable entry point?', ['package.json'])
            page = invoke(repo, 'read-input', run['run'], 'entry', 'package.json', '--count', '1')
            anchor = dict(path='package.json', content_id=page['content_id'], start=1, end=1)
            definitions = [
                dict(id='entry-context', title='CLI entry', summary='The package exposes the REA executable.',
                     terms=['launch'], content={'role': 'CLI entry'},
                     support=[dict(pointer='/role', evidence=[anchor])]),
                dict(id='execution-context', title='Execution', summary='The executable starts the launcher.',
                     terms=['execution'], content={'flow': 'launcher'},
                     support=[dict(pointer='/flow', evidence=[anchor])]),
            ]
            relations = [
                dict(source='file:package.json', relation='explained-by', target='entry-context',
                     condition='', evidence=[anchor]),
                dict(source='execution-context', relation='describes', target='file:package.json',
                     condition='', evidence=[anchor]),
            ]
            save(Path(run['shards']) / 'entry.json', dict(snapshot=run['snapshot']['identity'], question='entry',
                 status='answered', gap='', discoveries=definitions, claims=relations))
            accept(repo, run, 'entry')
            publish_investigation(repo, run)
            node = invoke(repo, 'node', 'file:package.json')['nodes'][0]
            contexts = node['related_discoveries']
            self.assertEqual(node['context_status'], 'linked')
            self.assertFalse(node['related_discoveries_truncated'])
            self.assertEqual({(c['key'], c['direction'], c['relation']) for c in contexts},
                             {('entry-context', 'outgoing', 'explained-by'),
                              ('execution-context', 'incoming', 'describes')})
            self.assertEqual({c['summary'] for c in contexts},
                             {'The package exposes the REA executable.', 'The executable starts the launcher.'})
            self.assertTrue(all(c['evidence'][0]['path'] == 'package.json' for c in contexts))
            self.assertEqual(invoke(repo, 'open', 'entry-context')['content']['role'], 'CLI entry')
            discovery = invoke(repo, 'node', 'entry-context')['nodes'][0]
            self.assertEqual(discovery['context_status'], 'self')
            self.assertEqual(discovery['discovery']['content']['role'], 'CLI entry')
            unrelated = invoke(repo, 'node', 'file:other.js')['nodes'][0]
            self.assertEqual(unrelated['related_discoveries'], [])
            self.assertEqual(unrelated['context_status'], 'not-linked')
            context_counts = invoke(repo, 'coverage', '--summary')['semantic_context']
            self.assertEqual(context_counts['scope'], 'repository-wide')
            files = next(row for row in context_counts['nodes_by_kind'] if row['kind'] == 'file')
            self.assertEqual((files['linked'], files['not_linked']), (1, 2))
            self.assertEqual(files['total'], 3)
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

    def test_context_previews_are_bounded_and_explicitly_truncated(self):
        with test_directory() as repo:
            revision = fixture(repo, {'index.js': 'export const start = () => 1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'entry', 'Which facts describe the entry?', ['index.js'])
            page = invoke(repo, 'read-input', run['run'], 'entry', 'index.js', '--count', '1')
            anchor = dict(path='index.js', content_id=page['content_id'], start=1, end=1)
            findings = [dict(id=f'finding-{i}', title=f'Finding {i}', summary='Context ' + 'x' * 400,
                             terms=['entry'], content={'index': i},
                             support=[dict(pointer='/index', evidence=[anchor])]) for i in range(9)]
            links = [dict(source=finding['id'], relation='describes', target='file:index.js',
                          condition='when started', evidence=[anchor]) for finding in findings]
            save(Path(run['shards']) / 'entry.json', dict(snapshot=run['snapshot']['identity'], question='entry',
                 status='answered', gap='', discoveries=findings, claims=links))
            accept(repo, run, 'entry')
            publish_investigation(repo, run)
            node = invoke(repo, 'node', 'file:index.js')['nodes'][0]
            self.assertEqual(node['context_status'], 'linked')
            self.assertEqual(len(node['related_discoveries']), 8)
            self.assertTrue(node['related_discoveries_truncated'])
            for context in node['related_discoveries']:
                self.assertLessEqual(len(context['summary']), 320)
                self.assertEqual(context['conditions'], ['when started'])
                self.assertTrue(context['relation_id'])


if __name__ == '__main__':
    unittest.main()
