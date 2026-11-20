from contextlib import closing
import json
from pathlib import Path
import sqlite3
import unittest
from uuid import uuid4

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, load, publish_investigation, save, write_answer


class CredentialPublication(unittest.TestCase):
    def test_sensitive_source_locator_publishes_without_its_value(self):
        repo = self.enterContext(test_directory())
        marker = 'synthetic-credential-' + uuid4().hex
        revision = fixture(repo, {'settings.env': f'REPORT_TOKEN={marker}\n',
                                  'report.py': 'token = settings["REPORT_TOKEN"]\n'})
        run = invoke(repo, 'investigate', '--commit', revision)
        add_question(run, 'report', 'Which credential does the report process read?', ['report.py'])
        refs = {}
        for path in ('settings.env', 'report.py'):
            page = invoke(repo, 'read-input', run['run'], 'report', path, '--count', '1')
            refs[path] = dict(path=path, content_id=page['content_id'], start=1, end=1)
            if path == 'settings.env':
                self.assertEqual(page['lines'], [f'REPORT_TOKEN={marker}'])

        shard = write_answer(run, 'report', [dict(source='process:report', relation='reads',
                             target='setting:REPORT_TOKEN', condition='', evidence=list(refs.values()))])
        content = {'reference': 'settings.env defines REPORT_TOKEN.',
                   'consumer': 'report.py reads REPORT_TOKEN from settings.'}
        discovery = dict(id='report-credential', title='Report credential lookup',
                         summary='The report reads a named credential.', terms=['REPORT_TOKEN'],
                         content=content, support=[
                             dict(pointer='/reference', evidence=[refs['settings.env']]),
                             dict(pointer='/consumer', evidence=[refs['report.py']])])
        save(shard, dict(load(shard), discoveries=[discovery]))
        accept(repo, run, 'report')
        graph = Path(publish_investigation(repo, run)['path'])
        self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')
        search = invoke(repo, 'search', 'REPORT_TOKEN')
        self.assertEqual([hit['key'] for hit in search['matches']], [discovery['id']])
        opened = invoke(repo, 'open', search['matches'][0]['key'])
        self.assertEqual(opened['content'], content)
        self.assertNotIn(marker, json.dumps([search, opened]))
        support = {entry['pointer']: entry['evidence'] for entry in opened['support']}
        for pointer, path in [('/reference', 'settings.env'), ('/consumer', 'report.py')]:
            locator, = support[pointer]
            self.assertEqual((locator['path'], locator['content_id']), (path, refs[path]['content_id']))
            self.assertEqual(locator['span'], [1, 0, 1, len((repo / path).read_text().splitlines()[0])])
        with closing(sqlite3.connect(graph)) as db:
            embedded, = db.execute("SELECT value FROM metadata WHERE key='accepted_shards'").fetchone()
            self.assertEqual(json.loads(embedded)['report'], load(shard))
            self.assertNotIn(marker, embedded)
            dump = '\n'.join(db.iterdump())
            self.assertIn('setting:REPORT_TOKEN', dump)
            self.assertNotIn(marker, dump)
        for artifact in graph.parent.rglob('*'):
            if artifact.is_file():
                with self.subTest(artifact=artifact.name):
                    self.assertNotIn(marker.encode(), artifact.read_bytes())
