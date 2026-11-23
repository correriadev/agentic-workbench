"""Grounded semantic node views do not invent, merge, or overstate context."""

from pathlib import Path
import unittest

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, publish_investigation, save


class SemanticNodeProjection(unittest.TestCase):
    def test_fields_keep_support_and_conflicting_discoveries_separate(self):
        with test_directory() as repo:
            revision = fixture(repo, {'package.json': '{"bin":{"rea":"scripts/rea.mjs"}}\n',
                                      'scripts/rea.mjs': 'export const main = () => 1;\n',
                                      'other.js': 'export const other = 1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'entry', 'What is the entry role and what remains unknown?', ['package.json'])
            page = invoke(repo, 'read-input', run['run'], 'entry', 'package.json', '--count', '1')
            anchor = dict(path='package.json', content_id=page['content_id'], start=1, end=1)
            definitions = [
                dict(id='entry-context', title='CLI entry', summary='The package declares a CLI entry.',
                     terms=['entry'], content={'role': 'CLI entry', 'behavior': 'Starts the launcher',
                                               'dependencies': [{'node': 'file:scripts/rea.mjs',
                                                                 'unverified': 'must not leak'}],
                                               'gaps': ['Runtime behavior remains unknown.'],
                                               'unrelated': 'not part of this projection'},
                     support=[dict(pointer=p, evidence=[anchor]) for p in
                              ['/role', '/behavior', '/dependencies/0/node', '/gaps']]),
                dict(id='alternate-context', title='Alternate context', summary='A distinct view.',
                     terms=['entry'], content={'role': 'Another role'},
                     support=[dict(pointer='/role', evidence=[anchor])]),
                dict(id='other-context', title='Referenced only', summary='Not a description of this node.',
                     terms=['entry'], content={'role': 'Must not be attributed'},
                     support=[dict(pointer='/role', evidence=[anchor])]),
            ]
            links = [dict(source='entry-context', relation='describes', target='file:package.json',
                          condition='', evidence=[anchor]),
                     dict(source='file:package.json', relation='explained-by', target='alternate-context',
                          condition='for another flow', evidence=[anchor]),
                     dict(source='other-context', relation='uses', target='file:package.json',
                          condition='', evidence=[anchor])]
            save(Path(run['shards']) / 'entry.json', dict(snapshot=run['snapshot']['identity'], question='entry',
                 status='partial', gap='Execution and other consumers remain unknown.',
                 discoveries=definitions, claims=links))
            accept(repo, run, 'entry')
            publish_investigation(repo, run)

            node = invoke(repo, 'node', 'file:package.json')['nodes'][0]
            self.assertEqual(node['context_status'], 'linked')  # legacy projection is unchanged
            self.assertIn('semantic_context', node)
            context = node['semantic_context']
            self.assertEqual(context['status'], 'partial')
            entries = {entry['discovery']: entry for entry in context['entries']}
            self.assertEqual(set(entries), {'entry-context', 'alternate-context'})
            first = entries['entry-context']
            self.assertEqual(first['fields']['role'][0]['value'], 'CLI entry')
            self.assertEqual(first['fields']['role'][0]['evidence'][0]['path'], 'package.json')
            self.assertEqual(first['fields']['dependencies'][0]['pointer'], '/dependencies/0/node')
            self.assertEqual(first['fields']['dependencies'][0]['value'], 'file:scripts/rea.mjs')
            self.assertNotIn('must not leak', repr(context))
            self.assertEqual(first['fields']['gaps'][0]['value'], ['Runtime behavior remains unknown.'])
            self.assertEqual(entries['alternate-context']['fields']['role'][0]['value'], 'Another role')
            self.assertEqual(entries['alternate-context']['conditions'], ['for another flow'])
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

            unrelated = invoke(repo, 'node', 'file:other.js')['nodes'][0]['semantic_context']
            self.assertEqual(unrelated['status'], 'not-linked')
            self.assertEqual(unrelated['entries'], [])

    def test_unsubstantiated_fields_are_not_presented_as_facts(self):
        with test_directory() as repo:
            revision = fixture(repo, {'index.js': 'export const start = () => 1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'entry', 'What does the entry define?', ['index.js'])
            page = invoke(repo, 'read-input', run['run'], 'entry', 'index.js', '--count', '1')
            anchor = dict(path='index.js', content_id=page['content_id'], start=1, end=1)
            finding = dict(id='entry', title='Entry', summary='An export exists.', terms=['entry'],
                           content={'role': 'Entry point', 'behavior': 'Unsubstantiated behavior'},
                           support=[dict(pointer='/role', evidence=[anchor])])
            link = dict(source='entry', relation='describes', target='file:index.js', condition='', evidence=[anchor])
            save(Path(run['shards']) / 'entry.json', dict(snapshot=run['snapshot']['identity'], question='entry',
                 status='answered', gap='', discoveries=[finding], claims=[link]))
            accept(repo, run, 'entry')
            publish_investigation(repo, run)
            node = invoke(repo, 'node', 'file:index.js')['nodes'][0]
            self.assertIn('semantic_context', node)
            context = node['semantic_context']
            self.assertEqual(context['status'], 'partial')
            self.assertEqual(context['entries'][0]['unsupported_fields'], ['behavior'])
            self.assertNotIn('behavior', context['entries'][0]['fields'])
            self.assertNotIn('Unsubstantiated behavior', repr(context))


if __name__ == '__main__':
    unittest.main()
