import hashlib
import json
import unittest

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, publish_investigation, save
from pathlib import Path


class ExportJSON(unittest.TestCase):
    def test_export_retains_semantic_content_and_its_source_pointer(self):
        with test_directory() as repo:
            rev = fixture(repo, {'cli.js': 'export const go = () => 1;\n'})
            invoke(repo, 'map', '--commit', rev)
            run = invoke(repo, 'investigate', '--commit', rev)
            add_question(run, 'context', 'What is the entry role?', ['cli.js'])
            page = invoke(repo, 'read-input', run['run'], 'context', 'cli.js', '--count', '1')
            ref = dict(path='cli.js', content_id=page['content_id'], start=1, end=1)
            discovery = dict(id='entry-role', title='Entry', summary='Entry role', terms=['entry'],
                             content={'role': 'Returns one.'}, support=[dict(pointer='/role', evidence=[ref])])
            claim = dict(source='entry-role', relation='describes', target='file:cli.js', condition='', evidence=[ref])
            save(Path(run['shards']) / 'context.json', dict(snapshot=run['snapshot']['identity'],
                 question='context', status='answered', gap='', discoveries=[discovery], claims=[claim]))
            accept(repo, run, 'context')
            publish_investigation(repo, run)
            invoke(repo, 'export', '--output', 'semantic.json')
            tables = json.loads((repo / '.project-mapper/semantic.json').read_text())['tables']
            self.assertEqual(tables['discoveries'][0]['content']['role'], 'Returns one.')
            self.assertEqual(tables['discovery_support'][0]['pointer'], '/role')
            self.assertTrue(any(o['content_id'] == page['content_id'] for o in tables['occurrences']))

    def test_full_export_is_a_read_only_snapshot_and_refuses_overwrite(self):
        with test_directory() as repo:
            rev = fixture(repo, {'package.json': '{"bin":{"demo":"cli.js"}}\n',
                                 'cli.js': 'export const go = () => 1;\n'})
            invoke(repo, 'map', '--commit', rev)
            graph = repo / '.project-mapper/graph.sqlite'
            before = hashlib.sha256(graph.read_bytes()).digest()
            result = invoke(repo, 'export', '--output', 'map.json')
            output = repo / '.project-mapper/map.json'
            data = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(result['path'], str(output))
            self.assertEqual(data['metadata']['snapshot']['revision'], rev)
            self.assertTrue(any(n['key'] == 'file:cli.js' for n in data['tables']['nodes']))
            self.assertTrue(data['tables']['relationship_observations'])
            self.assertEqual(hashlib.sha256(graph.read_bytes()).digest(), before)
            self.assertNotEqual(invoke(repo, 'export', '--output', 'map.json', ok=False).returncode, 0)
            self.assertNotEqual(invoke(repo, 'export', '--output', '../outside.json', ok=False).returncode, 0)
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

    def test_dimension_export_keeps_relationship_endpoints_and_evidence(self):
        with test_directory() as repo:
            rev = fixture(repo, {'package.json': '{"bin":{"demo":"cli.js"}}\n',
                                 'cli.js': 'export const go = () => 1;\n',
                                 'other.js': 'export const other = () => 2;\n'})
            invoke(repo, 'map', '--commit', rev)
            invoke(repo, 'export', '--output', 'entrypoints.json', '--dimension', 'entrypoint')
            data = json.loads((repo / '.project-mapper/entrypoints.json').read_text(encoding='utf-8'))
            self.assertEqual(data['selection']['dimension'], 'entrypoint')
            nodes = {row['key'] for row in data['tables']['nodes']}
            self.assertIn('file:cli.js', nodes)
            self.assertNotIn('file:other.js', nodes)
            for edge in data['tables']['relationships']:
                self.assertIn(edge['source'], nodes)
                if edge['target'] is not None:
                    self.assertIn(edge['target'], nodes)
            self.assertTrue(data['tables']['relationship_observations'])
            self.assertNotEqual(invoke(repo, 'export', '--output', 'bad.json', '--dimension', 'missing', ok=False).returncode, 0)


if __name__ == '__main__':
    unittest.main()
