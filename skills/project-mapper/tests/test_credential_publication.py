from contextlib import closing
from pathlib import Path
import sqlite3
import unittest
from uuid import uuid4

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, publish_investigation, write_answer


class CredentialPublication(unittest.TestCase):
    def test_sensitive_source_locator_publishes_without_its_value(self):
        repo = self.enterContext(test_directory())
        marker = 'synthetic-credential-' + uuid4().hex
        revision = fixture(repo, {'settings.env': f'REPORT_TOKEN={marker}\n',
                                  'report.py': 'token = settings["REPORT_TOKEN"]\n'})
        run = invoke(repo, 'investigate', '--commit', revision)
        add_question(run, 'report', 'Which credential does the report process read?', ['report.py'])
        refs = []
        for path in ('settings.env', 'report.py'):
            page = invoke(repo, 'read-input', run['run'], 'report', path, '--count', '1')
            refs.append(dict(path=path, content_id=page['content_id'], start=1, end=1))
            if path == 'settings.env':
                self.assertIn(marker, page['lines'][0])

        write_answer(run, 'report', [dict(source='process:report', relation='reads',
                                          target='setting:REPORT_TOKEN', condition='', evidence=refs)])
        accept(repo, run, 'report')
        graph = Path(publish_investigation(repo, run)['path'])
        self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')
        with closing(sqlite3.connect(graph)) as db:
            dump = '\n'.join(db.iterdump())
            self.assertIn('accepted_shards', dump)
            self.assertIn('setting:REPORT_TOKEN', dump)
            self.assertNotIn(marker, dump)
        for artifact in graph.parent.rglob('*'):
            if artifact.is_file():
                with self.subTest(artifact=artifact.name):
                    self.assertNotIn(marker.encode(), artifact.read_bytes())
