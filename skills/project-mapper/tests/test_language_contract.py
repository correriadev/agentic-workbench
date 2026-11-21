from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import unittest

from test_acceptance import SCRIPTS, fixture, invoke, test_directory
from test_investigation import accept, add_question, load, publish_investigation, save, write_answer

sys.path.insert(0, str(SCRIPTS))
import graph_store
from investigation import compile_investigation
from scan_files import digest, snapshot_reader


class LanguageContract(unittest.TestCase):
    source = 'São Paulo = SP\n'

    def setUp(self):
        self.repo = self.enterContext(test_directory())
        self.rev = fixture(self.repo, {'estados.txt': self.source})
        self.run = invoke(self.repo, 'investigate', '--commit', self.rev)
        add_question(self.run, 'lookup', 'What code identifies São Paulo?', ['estados.txt'])
        self.plan = load(self.run['plan'])
        self.question = self.plan['questions'][0]
        page = self.cli('read-input', 'lookup', 'estados.txt')
        citation = dict(path=page['path'], content_id=page['content_id'], start=1, end=1)
        claim = dict(source='state:São Paulo', target='code:SP', relation='uses',
                     condition='', evidence=[citation])
        self.shard = write_answer(self.run, 'lookup', [claim])

    def cli(self, command, *args, ok=True):
        return invoke(self.repo, command, self.run['run'], *args, ok=ok)

    def test_review_is_explicit_retryable_and_bound_to_the_new_policy(self):
        self.assertEqual(self.plan.get('output_language'), 'en')
        fingerprint = self.cli('check-shard', 'lookup')['fingerprint']
        refused = self.cli('accept', 'lookup', fingerprint, ok=False)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('--reviewed-english', refused.stderr)
        self.assertEqual(load(self.run['decisions']), {})

        # This is the decision format used before the English authoring contract.
        old = digest([self.question, load(self.shard), {}])
        save(self.run['decisions'], {'lookup': old})
        self.assertNotEqual(fingerprint, old)
        self.assertNotEqual(publish_investigation(self.repo, self.run, ok=False).returncode, 0)
        self.assertNotEqual(self.cli('accept', 'lookup', old, '--reviewed-english', ok=False).returncode, 0)
        self.assertEqual(load(self.run['decisions']), {'lookup': old})
        for _ in range(2):
            self.cli('accept', 'lookup', fingerprint, '--reviewed-english')
            self.assertEqual(publish_investigation(self.repo, self.run)['status'], 'complete')
        readme = (self.repo / '.project-mapper/README.md').read_text(encoding='utf-8')
        self.assertIn('English', readme)
        self.assertEqual(self.cli('read-input', 'lookup', 'estados.txt', '--count', '1')['lines'], self.source.splitlines())
        self.assertEqual(invoke(self.repo, 'node', 'state:São Paulo')['nodes'][0]['name'], 'São Paulo')

    def test_publication_requires_review_of_every_question_even_without_a_shard(self):
        reviewed = self.cli('check-plan')
        self.assertEqual(reviewed['plan'], self.plan)
        initial = self.cli('publish', ok=False)
        self.assertNotEqual(initial.returncode, 0)
        self.assertIn('--reviewed-english-plan', initial.stderr)
        self.assertFalse((self.repo / '.project-mapper/graph.sqlite').exists())
        published = self.cli('publish', '--reviewed-english-plan', reviewed['fingerprint'])
        self.assertEqual(published['status'], 'partial')
        self.assertEqual(published['investigation_scope']['answered'], 0)

        accept(self.repo, self.run, 'lookup')
        add_question(self.run, 'new-question', 'Qual é a entrada?', ['estados.txt'])
        before = Path(published['path']).read_bytes()
        after_append = self.cli('publish', '--reviewed-english-plan', reviewed['fingerprint'], ok=False)
        self.assertNotEqual(after_append.returncode, 0)
        self.assertEqual(Path(published['path']).read_bytes(), before)
        mixed = self.cli('check-plan')
        self.assertEqual(mixed['plan']['questions'][-1]['question'], 'Qual é a entrada?')
        fixed = mixed['plan']
        fixed['questions'][-1]['question'] = 'Which input selects the state?'
        save(self.run['plan'], fixed)
        after_edit = self.cli('publish', '--reviewed-english-plan', mixed['fingerprint'], ok=False)
        self.assertNotEqual(after_edit.returncode, 0)
        self.assertEqual(Path(published['path']).read_bytes(), before)
        partial = publish_investigation(self.repo, self.run)
        self.assertEqual(partial['status'], 'partial')
        self.assertEqual(partial['investigation_scope']['answered'], 1)
        self.assertEqual(invoke(self.repo, 'verify')['integrity'], 'ok')

    def test_new_work_requires_the_declaration_but_legacy_sources_stay_readable(self):
        for language in (None, 'pt-BR'):
            with self.subTest(language=language):
                plan = dict(self.plan, output_language=language)
                if language is None:
                    del plan['output_language']
                save(self.run['plan'], plan)
                if language is None:
                    self.assertEqual(self.cli('read-input', '@', 'estados.txt', '--count', '1')['lines'], self.source.splitlines())
                    self.assertEqual(self.cli('search-input', 'São')['matches'][0]['path'], 'estados.txt')
                for command in [('worker-prompt', 'lookup'), ('check-shard', 'lookup'),
                                ('accept', 'lookup', 'old-digest', '--reviewed-english'), ('publish',)]:
                    failed = self.cli(*command, ok=False)
                    self.assertNotEqual(failed.returncode, 0)
                    self.assertIn('output_language', failed.stderr)

    def test_legacy_publication_replays_and_survives_upgrade_with_missing_approval(self):
        # Both versions cite the same source path and literal. The question and its ID are translated.
        old_question = dict(self.question, id='consulta', question='Qual código identifica São Paulo?')
        old_plan = dict(snapshot=self.plan['snapshot'], questions=[old_question])
        old_shards = {'consulta': dict(load(self.shard), question='consulta')}
        manifest = load(self.run['inventory'])
        db = self.repo / '.project-mapper' / 'graph.sqlite'
        with snapshot_reader(self.repo, manifest) as reader:
            graph_store.write(db, compile_investigation(manifest, old_plan, old_shards, reader, allow_legacy=True))
        before = db.read_bytes()
        self.assertEqual(invoke(self.repo, 'verify')['status'], 'complete')
        self.assertEqual(db.read_bytes(), before)
        refused = publish_investigation(self.repo, self.run, ok=False)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('partial', refused.stderr)
        self.assertEqual(db.read_bytes(), before)
        accept(self.repo, self.run, 'lookup')
        self.assertEqual(publish_investigation(self.repo, self.run)['status'], 'complete')
        with closing(sqlite3.connect(db)) as conn:
            saved = json.loads(conn.execute("SELECT value FROM metadata WHERE key='plan'").fetchone()[0])
        self.assertEqual(saved, self.plan)
        # An expanded plan must not replace the complete migrated map with partial coverage.
        upgraded = db.read_bytes()
        add_question(self.run, 'owner', 'Who assigns the state codes?', ['estados.txt'])
        refused = publish_investigation(self.repo, self.run, ok=False)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('active complete graph preserved', refused.stderr)
        self.assertEqual(db.read_bytes(), upgraded)
