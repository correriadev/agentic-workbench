"""Long authored metadata remains accessible without bloating the projected context."""

from pathlib import Path
import unittest

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, publish_investigation, save


class SemanticNodeLongValues(unittest.TestCase):
    def test_long_title_subject_and_condition_are_bounded_and_originals_remain_accessible(self):
        with test_directory() as repo:
            revision = fixture(repo, {'entry.js': 'export const start = () => 1;\n'})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'entry', 'What is this entry?', ['entry.js'])
            page = invoke(repo, 'read-input', run['run'], 'entry', 'entry.js', '--count', '1')
            anchor = dict(path='entry.js', content_id=page['content_id'], start=1, end=1)
            long_subject = 'unknown:' + 's' * 3000
            long_condition = 'c' * 3000
            long_title = 'Title ' + 't' * 500
            findings = [
                dict(id='large-title', title=long_title, summary='Entry.', terms=['entry'],
                     content={'subject_node': 'file:entry.js', 'role': 'Entry point'},
                     support=[dict(pointer='', evidence=[anchor])]),
                dict(id='large-subject', title='Other', summary='Other subject.', terms=['other'],
                     content={'subject_node': long_subject, 'role': 'Other point'},
                     support=[dict(pointer='', evidence=[anchor])]),
            ]
            claims = [dict(source='large-title', relation='describes', target='file:entry.js',
                           condition=long_condition, evidence=[anchor]),
                      dict(source='large-subject', relation='describes', target='file:entry.js',
                           condition='', evidence=[anchor])]
            save(Path(run['shards']) / 'entry.json', dict(snapshot=run['snapshot']['identity'], question='entry',
                 status='answered', gap='', discoveries=findings, claims=claims))
            accept(repo, run, 'entry')
            publish_investigation(repo, run)
            node = invoke(repo, 'node', 'file:entry.js')['nodes'][0]
            context = node['semantic_context']
            entries = {entry['discovery']: entry for entry in context['entries']}
            first = entries['large-title']
            self.assertTrue(first['title_truncated'])
            self.assertLessEqual(len(first['title']), 160)
            self.assertTrue(first['conditions_omitted'])
            self.assertIsNone(first['conditions'])
            self.assertTrue(first['relation_evidence'][0]['limitation_omitted'])
            self.assertEqual(context['node_role_status'], 'partial')
            second = entries['large-subject']
            self.assertTrue(second['subject_node_omitted'])
            self.assertNotIn('subject_node', second)
            self.assertEqual(invoke(repo, 'open', 'large-title')['title'], long_title)
            self.assertEqual(invoke(repo, 'open', 'large-subject')['content']['subject_node'], long_subject)
            relation = next(edge for edge in node['incoming'] if edge['source'] == 'large-title')
            self.assertEqual(relation['conditions'], [long_condition])


if __name__ == '__main__':
    unittest.main()
