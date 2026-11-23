import unittest

from test_acceptance import fixture, invoke, test_directory
from test_investigation import FILES, add_question, evidence, invokes, load, save, write_answer


class Preflight(unittest.TestCase):
    def test_stale_requirement_invalidates_accept_and_scoped_absence_stays_valid(self):
        with test_directory() as repo:
            rev = fixture(repo, FILES)
            run = invoke(repo, 'investigate', '--commit', rev)
            add_question(run, 'override', 'Does this script override its command?', ['scripts/run.ps1'])
            locator = evidence(repo, run, 'override', 'scripts/run.ps1', 1, 5)
            shard = write_answer(run, 'override', [])
            raw = load(shard)
            raw['absence'] = dict(statement='No override within this script.', evidence=[locator])
            save(shard, raw)
            checked = invoke(repo, 'check-shard', run['run'], 'override')
            plan = load(run['plan'])
            plan['questions'][0]['required_relations'] = ['Trace any override within this script.']
            save(run['plan'], plan)
            draft = invoke(repo, 'preflight', run['run'], 'override')
            self.assertEqual(draft['unmapped'], plan['questions'][0]['required_relations'])
            self.assertEqual(draft['status'], 'answered')
            stale = invoke(repo, 'accept', run['run'], 'override', checked['fingerprint'],
                           '--reviewed-english', ok=False)
            self.assertIn('fingerprint changed', stale.stderr)
            self.assertEqual(load(run['decisions']), {})

    def test_draft_feedback_preserves_review_and_reports_unmapped_requirements(self):
        with test_directory() as repo:
            rev = fixture(repo, FILES)
            run = invoke(repo, 'investigate', '--commit', rev)
            add_question(run, 'upstream', 'Who produces the input?', ['package.json'])
            add_question(run, 'report', 'How is output used?', ['scripts/run.ps1'], ['upstream'])
            locator = evidence(repo, run, 'report', 'scripts/run.ps1', 3, 4)
            claim = invokes('file:scripts/run.ps1', 'file:generated/report', locator)
            shard = write_answer(run, 'report', [claim])
            plan = load(run['plan'])
            plan['questions'][1]['required_relations'] = ['Identify the writer.', 'Identify the consuming step.']
            save(run['plan'], plan)
            cmd = ('preflight', run['run'], 'report')
            failure = invoke(repo, *cmd, ok=False)
            self.assertIn('artifact:', failure.stderr)
            claim['target'] = 'artifact:generated/report'
            write_answer(run, 'report', [claim], status='partial', gap='Consumer remains unverified.')
            before = shard.read_bytes()
            result = invoke(repo, *cmd, '--covers', '1', '1')
            self.assertEqual(result['unmapped'], ['Identify the consuming step.'])
            self.assertEqual(result['mappings'][0]['claim'], claim)
            self.assertEqual(result['status'], 'partial')
            self.assertIn('outside', invoke(repo, *cmd, '--covers', '2', '2', ok=False).stderr)
            self.assertEqual(shard.read_bytes(), before)
            self.assertEqual(load(run['decisions']), {})
            self.assertIn('prerequisite', invoke(repo, 'check-shard', run['run'], 'report', ok=False).stderr)
            claim['evidence'][0]['end'] = 9999
            write_answer(run, 'report', [claim])
            self.assertIn('end of file', invoke(repo, *cmd, ok=False).stderr)
