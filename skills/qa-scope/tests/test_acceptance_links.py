"""Verify QA contracts link to real criteria in both supported scope formats."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILLS = Path(__file__).resolve().parents[2]
QA = SKILLS / 'qa-scope' / 'contract.py'
EXECUTOR = SKILLS / 'execute-scope' / 'contract.py'
PLANNER = SKILLS / 'new-scope' / 'contract.py'


class AcceptanceLinks(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.folder = self.root / 'docs' / 'specs' / 'payment'
        self.folder.mkdir(parents=True)

    def call(self, cli, *args, payload=None):
        return subprocess.run([sys.executable, str(cli), str(self.folder), *args],
                              input=json.dumps(payload) if payload is not None else None,
                              text=True, capture_output=True)

    def contract(self, acceptance):
        scope = (self.folder / 'SCOPE.md').read_bytes()
        return dict(change_id='payment', scope_revision=hashlib.sha256(scope).hexdigest(),
                    risk_coverage=[dict(risk_id='R1', obligation_ids=['QA-1'])],
                    obligations=[dict(id='QA-1', acceptance_ids=[acceptance], risk_ids=['R1'],
                                      failure_to_detect='Duplicate payment', preconditions=['One payment exists'],
                                      stimulus='Repeat the request', observables=['Payment rows'],
                                      assertions=['One payment'], environment='local', artifacts=['output'],
                                      source_refs=['payment.py'], blocking=True, status='ready', pending_reason=None)])

    def test_standalone_scope_accepts_existing_criterion_and_rejects_unknown_one(self):
        (self.folder / 'SCOPE.md').write_text('A1 Payment succeeds.\nR1 Duplicate payment.\n')
        for cli in (QA, EXECUTOR):
            with self.subTest(cli=cli):
                bad = self.call(cli, 'qa-plan', '--expect', 'absent', payload=self.contract('A999'))
                self.assertNotEqual(bad.returncode, 0, bad.stderr)
                self.assertIn('acceptance', bad.stderr.lower())
                good = self.call(cli, 'qa-plan', '--expect', 'absent', payload=self.contract('A1'))
                self.assertEqual(good.returncode, 0, good.stderr)
                (self.folder / 'qa.json').unlink()

    def test_standalone_scope_accepts_bold_list_and_table_criteria(self):
        for text in ('- **A1** — Payment succeeds.\nR1 Duplicate.\n',
                     '| A1 | Payment succeeds. |\n| R1 | Duplicate. |\n'):
            with self.subTest(scope=text):
                (self.folder / 'SCOPE.md').write_text(text)
                result = self.call(QA, 'qa-plan', '--expect', 'absent', payload=self.contract('A1'))
                self.assertEqual(result.returncode, 0, result.stderr)
                (self.folder / 'qa.json').unlink()

    def test_database_scope_checks_active_acceptance_nodes(self):
        init = self.call(PLANNER, 'init')
        self.assertEqual(init.returncode, 0, init.stderr)
        nodes = [dict(id=key, kind=kind, title=key, content=content,
                      state=state, origin='inference') for key, kind, content, state in [
            ('A-CANCEL', 'acceptance', 'Cancellation succeeds.', 'planned'),
            ('R1', 'risk', 'Duplicate cancellation.', 'applicable'),
            ('A-OLD', 'acceptance', 'Old criterion.', 'superseded')]]
        applied = self.call(PLANNER, 'apply', '--expect', '0',
                            payload=dict(request_id='initial', reason='Test QA linking', nodes=nodes))
        self.assertEqual(applied.returncode, 0, applied.stderr)
        rendered = self.call(PLANNER, 'render-scope')
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        for cli in (QA, EXECUTOR):
            with self.subTest(cli=cli):
                bad = self.call(cli, 'qa-plan', '--expect', 'absent', payload=self.contract('A-OLD'))
                self.assertNotEqual(bad.returncode, 0, bad.stderr)
                good = self.call(cli, 'qa-plan', '--expect', 'absent', payload=self.contract('A-CANCEL'))
                self.assertEqual(good.returncode, 0, good.stderr)
                (self.folder / 'qa.json').unlink()

        scope_path = self.folder / 'SCOPE.md'
        rendered_scope = scope_path.read_text()
        scope_path.write_text(rendered_scope.replace('**A-CANCEL —', '**A-OTHER —'))
        altered = self.call(QA, 'qa-plan', '--expect', 'absent', payload=self.contract('A-CANCEL'))
        self.assertNotEqual(altered.returncode, 0)
        self.assertFalse((self.folder / 'qa.json').exists())
        scope_path.write_text(rendered_scope)

        applied = self.call(PLANNER, 'apply', '--expect', '1', payload=dict(
            request_id='revision', reason='Change the specification',
            nodes=[dict(id='D1', kind='decision', title='Decision', content='A new decision.',
                        state='confirmed', origin='human')]))
        self.assertEqual(applied.returncode, 0, applied.stderr)
        stale = self.call(QA, 'qa-plan', '--expect', 'absent', payload=self.contract('A-CANCEL'))
        self.assertNotEqual(stale.returncode, 0)
        self.assertIn('revision', stale.stderr.lower())
        self.assertFalse((self.folder / 'qa.json').exists())


if __name__ == '__main__':
    unittest.main()
