"""A shared discovery's fields do not become facts about every linked node."""

from pathlib import Path
import unittest

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, publish_investigation, save


class SemanticContextScope(unittest.TestCase):
    def test_one_flow_can_contextualize_multiple_nodes_without_relabeling_them(self):
        with test_directory() as repo:
            revision = fixture(repo, {'handler.js': 'export const handler = () => 1;\n',
                                      'settings.js': 'export const limit = 1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'flow', 'What does this flow contain?', ['handler.js', 'settings.js'])
            page = invoke(repo, 'read-input', run['run'], 'flow', 'handler.js', '--count', '1')
            ref = dict(path='handler.js', content_id=page['content_id'], start=1, end=1)
            discovery = dict(id='flow-context', title='Whole flow', summary='A flow uses a setting.',
                             terms=['flow'], content={'role': 'The feature processes a request.'},
                             support=[dict(pointer='/role', evidence=[ref])])
            links = [dict(source='flow-context', relation='describes', target='file:' + path,
                          condition='', evidence=[ref]) for path in ('handler.js', 'settings.js')]
            save(Path(run['shards']) / 'flow.json', dict(snapshot=run['snapshot']['identity'], question='flow',
                 status='answered', gap='', discoveries=[discovery], claims=links))
            accept(repo, run, 'flow')
            publish_investigation(repo, run)
            for path in ('handler.js', 'settings.js'):
                context = invoke(repo, 'node', 'file:' + path)['nodes'][0]['semantic_context']
                self.assertIn('not automatically attributes of this node', context['basis'])
                self.assertEqual(context['node_role_status'], 'not-linked')
                entry = context['entries'][0]
                self.assertEqual(entry['field_scope'], 'discovery')
                self.assertEqual(entry['discovery'], 'flow-context')
                self.assertEqual(entry['fields']['role'][0]['value'], 'The feature processes a request.')
                self.assertNotIn('role', context)


if __name__ == '__main__':
    unittest.main()
