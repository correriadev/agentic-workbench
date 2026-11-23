"""Node-specific attribution requires an evidenced explicit subject and role."""

from pathlib import Path
import unittest

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, publish_investigation, save


class SemanticNodeSubject(unittest.TestCase):
    def test_empty_or_null_role_is_not_attributed_to_the_node(self):
        with test_directory() as repo:
            revision = fixture(repo, {'handler.js': 'export const handler = () => 1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'context', 'What is the handler role?', ['handler.js'])
            page = invoke(repo, 'read-input', run['run'], 'context', 'handler.js', '--count', '1')
            evidence = dict(path='handler.js', content_id=page['content_id'], start=1, end=1)
            findings = [dict(id=f'role-{index}', title='Handler', summary='Handler context.', terms=['handler'],
                             content={'subject_node': 'file:handler.js', 'role': value},
                             support=[dict(pointer='', evidence=[evidence])])
                        for index, value in enumerate(('', None, '   '))]
            claims = [dict(source=finding['id'], relation='describes', target='file:handler.js',
                           condition='', evidence=[evidence]) for finding in findings]
            save(Path(run['shards']) / 'context.json', dict(snapshot=run['snapshot']['identity'],
                 question='context', status='answered', gap='', discoveries=findings, claims=claims))
            accept(repo, run, 'context')
            publish_investigation(repo, run)
            context = invoke(repo, 'node', 'file:handler.js')['nodes'][0]['semantic_context']
            self.assertEqual(context['status'], 'partial')
            self.assertEqual(context['node_role_status'], 'not-linked')
            self.assertTrue(all(entry['field_scope'] == 'discovery' for entry in context['entries']))

    def test_node_role_status_remains_partial_when_question_has_gap(self):
        with test_directory() as repo:
            revision = fixture(repo, {'handler.js': 'export const handler = () => 1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'context', 'What does the handler do?', ['handler.js'])
            page = invoke(repo, 'read-input', run['run'], 'context', 'handler.js', '--count', '1')
            evidence = dict(path='handler.js', content_id=page['content_id'], start=1, end=1)
            discovery = dict(id='handler-context', title='Handler', summary='Handler context.', terms=['handler'],
                             content={'subject_node': 'file:handler.js', 'role': 'Handles input.'},
                             support=[dict(pointer='', evidence=[evidence])])
            claim = dict(source='handler-context', relation='describes', target='file:handler.js',
                         condition='', evidence=[evidence])
            save(Path(run['shards']) / 'context.json', dict(snapshot=run['snapshot']['identity'],
                 question='context', status='partial', gap='Error handling remains unknown.',
                 discoveries=[discovery], claims=[claim]))
            accept(repo, run, 'context')
            publish_investigation(repo, run)
            context = invoke(repo, 'node', 'file:handler.js')['nodes'][0]['semantic_context']
            self.assertEqual(context['node_role_status'], 'partial')
            self.assertEqual(context['entries'][0]['field_scope'], 'node')

    def test_shared_flow_and_node_specific_roles_remain_distinct(self):
        with test_directory() as repo:
            revision = fixture(repo, {'handler.js': 'export const handler = () => 1;\n',
                                      'settings.js': 'export const limit = 1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'context', 'Which roles were assigned?', ['handler.js', 'settings.js'])
            page = invoke(repo, 'read-input', run['run'], 'context', 'handler.js', '--count', '1')
            evidence = dict(path='handler.js', content_id=page['content_id'], start=1, end=1)

            def finding(identifier, content, pointers):
                return dict(id=identifier, title=identifier, summary='Context.', terms=['context'],
                            content=content, support=[dict(pointer=p, evidence=[evidence]) for p in pointers])

            findings = [
                finding('shared-flow', {'role': 'The flow processes input.'}, ['/role']),
                finding('handler-role', {'subject_node': 'file:handler.js', 'role': 'Handles input.'},
                        ['/subject_node', '/role']),
                finding('settings-role', {'subject_node': 'file:settings.js', 'role': 'Provides settings.'}, ['']),
                finding('unsupported-subject', {'subject_node': 'file:handler.js', 'role': 'Unattributed.'}, ['/role']),
                finding('unsupported-role', {'subject_node': 'file:handler.js', 'role': 'Unsubstantiated.'},
                        ['/subject_node']),
            ]
            claims = [dict(source=finding['id'], relation='describes', target='file:' + path,
                           condition='', evidence=[evidence]) for finding in findings
                      for path in ('handler.js', 'settings.js')]
            save(Path(run['shards']) / 'context.json', dict(snapshot=run['snapshot']['identity'],
                 question='context', status='answered', gap='', discoveries=findings, claims=claims))
            accept(repo, run, 'context')
            publish_investigation(repo, run)

            handler = invoke(repo, 'node', 'file:handler.js')['nodes'][0]['semantic_context']
            setting = invoke(repo, 'node', 'file:settings.js')['nodes'][0]['semantic_context']
            self.assertEqual(handler['status'], 'partial')
            self.assertEqual(handler['node_role_status'], 'partial')
            self.assertEqual(setting['node_role_status'], 'reviewed')
            first = {entry['discovery']: entry for entry in handler['entries']}
            second = {entry['discovery']: entry for entry in setting['entries']}
            for entries in (first, second):
                self.assertEqual(entries['shared-flow']['field_scope'], 'discovery')
                self.assertEqual(entries['shared-flow']['subject_relation'], 'shared')
                self.assertEqual(entries['unsupported-subject']['field_scope'], 'discovery')
                self.assertEqual(entries['unsupported-subject']['subject_relation'], 'unsupported')
                self.assertNotIn('subject_node', entries['unsupported-subject'])
                self.assertEqual(entries['unsupported-role']['field_scope'], 'discovery')
                self.assertNotIn('role', entries['unsupported-role']['fields'])
            self.assertEqual((first['handler-role']['field_scope'], second['handler-role']['field_scope']),
                             ('node', 'discovery'))
            self.assertEqual((first['settings-role']['field_scope'], second['settings-role']['field_scope']),
                             ('discovery', 'node'))
            self.assertEqual(first['handler-role']['subject_node'], 'file:handler.js')
            self.assertEqual(first['handler-role']['subject_support'][0]['pointer'], '/subject_node')
            self.assertEqual(second['settings-role']['subject_support'][0]['support_pointer'], '')
            self.assertEqual(second['settings-role']['subject_relation'], 'same-node')
            self.assertEqual(first['settings-role']['subject_relation'], 'other-node')
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')


if __name__ == '__main__':
    unittest.main()
