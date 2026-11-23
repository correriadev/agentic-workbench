"""Direct semantic context coverage matches the node projection."""

from pathlib import Path
import unittest

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, publish_investigation, save


class SemanticCoverage(unittest.TestCase):
    def test_non_contextual_links_are_not_counted_as_descriptions(self):
        with test_directory() as repo:
            revision = fixture(repo, {name: 'export const value = 1;\n' for name in ('a.js', 'b.js', 'c.js')})
            invoke(repo, 'map', '--commit', revision)
            run = invoke(repo, 'investigate', '--commit', revision)
            add_question(run, 'context', 'What describes these components?', ['a.js'])
            page = invoke(repo, 'read-input', run['run'], 'context', 'a.js', '--count', '1')
            anchor = dict(path='a.js', content_id=page['content_id'], start=1, end=1)
            finding = dict(id='context', title='Context', summary='Context for two nodes.', terms=['context'],
                           content={'role': 'A role'}, support=[dict(pointer='/role', evidence=[anchor])])
            relations = [dict(source='context', relation='describes', target='file:a.js', condition='', evidence=[anchor]),
                         dict(source='file:b.js', relation='explained-by', target='context', condition='', evidence=[anchor]),
                         dict(source='context', relation='uses', target='file:c.js', condition='', evidence=[anchor])]
            save(Path(run['shards']) / 'context.json', dict(snapshot=run['snapshot']['identity'],
                 question='context', status='answered', gap='', discoveries=[finding], claims=relations))
            accept(repo, run, 'context')
            publish_investigation(repo, run)
            counts = invoke(repo, 'coverage', '--summary')['semantic_context']
            files = next(row for row in counts['nodes_by_kind'] if row['kind'] == 'file')
            self.assertEqual((files['linked'], files['not_linked'], files['total']), (2, 1, 3))
            for path, status in [('a.js', 'reviewed'), ('b.js', 'reviewed'), ('c.js', 'not-linked')]:
                context = invoke(repo, 'node', 'file:' + path)['nodes'][0]['semantic_context']
                self.assertEqual(context['status'], status)
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')


if __name__ == '__main__':
    unittest.main()
