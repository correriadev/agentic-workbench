"""Projection bounds and evidence survive open discovery shapes."""

from pathlib import Path
import unittest

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, publish_investigation, save


class SemanticNodeLimits(unittest.TestCase):
    def test_unstructured_root_evidence_and_fragment_limits(self):
        with test_directory() as repo:
            revision = fixture(repo, {'entry.js': 'export const start = () => 1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'entry', 'What is associated with the entry?', ['entry.js'])
            page = invoke(repo, 'read-input', run['run'], 'entry', 'entry.js', '--count', '1')
            anchor = dict(path='entry.js', content_id=page['content_id'], start=1, end=1)
            def finding(name, content, pointers):
                return dict(id=name, title=name, summary='Observed entry context.', terms=['entry'],
                            content=content, support=[dict(pointer=p, evidence=[anchor]) for p in pointers])
            findings = [
                finding('unstructured', {'contract': 'unstructured fact'}, ['/contract']),
                finding('root-supported', {'role': 'Entry point', 'behavior': 'Calls the service'}, ['']),
                finding('many-fragments', {'dependencies': [f'component-{i}' for i in range(12)]},
                        [f'/dependencies/{i}' for i in range(12)]),
                finding('large-value', {'role': 'x' * 3000}, ['/role']),
            ]
            claims = [dict(source=f['id'], relation='describes', target='file:entry.js',
                           condition='', evidence=[anchor]) for f in findings]
            save(Path(run['shards']) / 'entry.json', dict(snapshot=run['snapshot']['identity'],
                 question='entry', status='answered', gap='', discoveries=findings, claims=claims))
            accept(repo, run, 'entry')
            publish_investigation(repo, run)

            context = invoke(repo, 'node', 'file:entry.js')['nodes'][0]['semantic_context']
            self.assertEqual(context['status'], 'partial')
            entries = {entry['discovery']: entry for entry in context['entries']}
            self.assertTrue(entries['unstructured']['additional_content'])
            self.assertEqual(entries['unstructured']['fields'], {})
            role = entries['root-supported']['fields']['role'][0]
            self.assertEqual((role['pointer'], role['support_pointer'], role['value']),
                             ('/role', '', 'Entry point'))
            self.assertEqual(role['evidence'][0]['content_id'], page['content_id'])
            self.assertEqual(len(entries['many-fragments']['fields']['dependencies']), 8)
            self.assertEqual(entries['many-fragments']['fragments_truncated'], ['dependencies'])
            self.assertTrue(entries['large-value']['value_truncated'])
            self.assertNotIn('value', entries['large-value']['fields']['role'][0])
            self.assertEqual(invoke(repo, 'open', 'large-value')['content']['role'], 'x' * 3000)


if __name__ == '__main__':
    unittest.main()
