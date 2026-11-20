import json
from pathlib import Path
import unittest

from test_acceptance import fixture, invoke, test_directory


# A declared npm shortcut is a decoy. The PowerShell runner directly launches Allure.
FILES = {
    'package.json': '{"scripts":{"e2e":"pwsh scripts/run.ps1","report":"allure generate"}}\n',
    'scripts/run.ps1': 'dotnet test tests/E2E.csproj\n'
                       "if (Get-ChildItem results -Filter '*-result.json') {\n"
                       '    node node_modules/allure/cli.js generate results\n'
                       '    node tools/verify.mjs report\n'
                       '}\n',
    'tests/E2E.csproj': '<Project Sdk="Microsoft.NET.Sdk" />\n',
    'tools/verify.mjs': 'import { existsSync } from "node:fs";\n'
                        'if (!existsSync("report/index.html")) process.exitCode = 1;\n',
}
FRESH = 'at least one *-result.json exists'


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    Path(path).write_text(json.dumps(value), encoding='utf-8')


def add_question(run, question_id, question, seeds, depends_on=()):
    plan = load(run['plan'])
    plan['questions'].append(dict(id=question_id, question=question, seeds=seeds, depends_on=list(depends_on)))
    save(run['plan'], plan)


def evidence(repo, run, question_id, path, start, end):
    page = invoke(repo, 'read-input', run['run'], question_id, path, '--start', str(start),
                  '--count', str(end - start + 1))
    expected = FILES[path].splitlines()[start - 1:end]
    if page['lines'] != expected:
        raise AssertionError(f'{path}:{start}-{end}: expected {expected}, got {page["lines"]}')
    return dict(path=path, content_id=page['content_id'], start=start, end=end)


def invokes(source, target, *citations, condition=''):
    return dict(source=source, relation='invokes', target=target, condition=condition, evidence=list(citations))


def write_answer(run, question_id, claims, *, status='answered', gap=''):
    shard = Path(run['plan']).parent / 'shards' / f'{question_id}.json'
    save(shard, dict(snapshot=load(run['plan'])['snapshot'], question=question_id,
                     status=status, claims=claims, gap=gap))
    return shard


def accept(repo, run, question_id):
    checked = invoke(repo, 'check-shard', run['run'], question_id)
    return invoke(repo, 'accept', run['run'], question_id, checked['fingerprint'], '--reviewed-english')


def publish_investigation(repo, run, *, ok=True):
    reviewed = invoke(repo, 'check-plan', run['run'])
    return invoke(repo, 'publish', run['run'], '--reviewed-english-plan', reviewed['fingerprint'], ok=ok)


def start_launch(repo, *snapshot_args):
    run = invoke(repo, 'investigate', *snapshot_args)
    add_question(run, 'launch', 'Which executable starts the tests?', ['package.json'])
    manifest = evidence(repo, run, 'launch', 'package.json', 1, 1)
    runner = evidence(repo, run, 'launch', 'scripts/run.ps1', 1, 1)
    first = invokes('npm:e2e', 'script:runner', manifest, runner)
    project = evidence(repo, run, 'launch', 'tests/E2E.csproj', 1, 1)
    second = invokes('script:runner', 'command:dotnet-test', runner, project)
    shard = write_answer(run, 'launch', [first, second])
    accept(repo, run, 'launch')
    return run, shard


class Investigation(unittest.TestCase):
    def test_supervisor_adds_question_and_publishes_conditional_cross_language_chain(self):
        with test_directory() as repo:
            rev = fixture(repo, FILES)
            run, _ = start_launch(repo, '--commit', rev)
            add_question(run, 'report', 'What triggers report generation and verification?',
                         ['scripts/run.ps1'], depends_on=['launch'])
            guard = evidence(repo, run, 'report', 'scripts/run.ps1', 2, 2)
            generate = evidence(repo, run, 'report', 'scripts/run.ps1', 3, 3)
            verify = evidence(repo, run, 'report', 'scripts/run.ps1', 4, 4)
            check = evidence(repo, run, 'report', 'tools/verify.mjs', 2, 2)
            write_answer(run, 'report', [invokes('script:runner', 'command:allure-generate',
                                                guard, generate, condition=FRESH),
                                         invokes('script:runner', 'script:verifier', guard, verify,
                                                 check, condition=FRESH)])
            accept(repo, run, 'report')
            published = publish_investigation(repo, run)
            verified = invoke(repo, 'verify')
            self.assertEqual(verified['snapshot']['revision'], rev)
            self.assertEqual(verified['integrity'], 'ok')
            scope = verified['investigation_scope']
            self.assertEqual(published['investigation_scope'], scope)
            self.assertEqual((scope['answered'], scope['questions']), (2, 2))
            self.assertEqual((scope['cited_files'], scope['eligible_files']), (4, 4))
            readme = (repo / '.project-mapper/README.md').read_text(encoding='utf-8')
            self.assertIn('complete for the planned questions', readme)
            self.assertIn('4 of 4 eligible files', readme)
            trace = invoke(repo, 'trace', 'npm:e2e', '--type', 'invokes', '--direction', 'out')
            edges = {(row['source'], row['target']): row for row in trace['edges']}
            self.assertEqual(set(edges), {
                ('npm:e2e', 'script:runner'), ('script:runner', 'command:dotnet-test'),
                ('script:runner', 'command:allure-generate'), ('script:runner', 'script:verifier'),
            })
            self.assertNotIn('npm:report', trace['nodes'])
            verifier = edges['script:runner', 'script:verifier']
            self.assertIn(FRESH, json.dumps(verifier['conditions']))
            self.assertEqual({anchor['path'] for anchor in verifier['evidence']},
                             {'scripts/run.ps1', 'tools/verify.mjs'})
            reverse = invoke(repo, 'trace', 'script:verifier', '--type', 'invokes', '--direction', 'in')
            self.assertIn('npm:e2e', reverse['nodes'])

    def test_unanswered_work_and_changed_proposal_cannot_certify_the_map(self):
        with test_directory() as repo:
            rev = fixture(repo, FILES)
            run, shard = start_launch(repo, '--commit', rev)
            add_question(run, 'deployment', 'Where is the runner deployed?', ['scripts/run.ps1'])
            add_question(run, 'hosted', 'Which hosted CI execution produced this report?', ['package.json'])
            gap = 'A hosted CI execution receipt is unavailable.'
            write_answer(run, 'hosted', [], status='partial', gap=gap)
            accept(repo, run, 'hosted')
            publish_investigation(repo, run)
            verified = invoke(repo, 'verify')
            self.assertEqual(verified['status'], 'partial')
            report = invoke(repo, 'coverage')
            self.assertEqual(report['investigation_scope']['answered'], 1)
            self.assertEqual(report['investigation_scope']['uncited_files'], 1)
            by_question = {row['task']: row for row in report['coverage']}
            self.assertEqual(by_question['deployment']['status'], 'unexamined')
            self.assertEqual(by_question['hosted']['reason'], gap)
            self.assertFalse(by_question['hosted']['scoped_absence'])

            previous = load(run['decisions'])
            answer = load(shard)
            # A changed claim can still have structurally valid source references.
            # Its previous acceptance must not authorize the new endpoint.
            answer['claims'][0]['target'] = 'npm:report'
            save(shard, answer)
            rejected = invoke(repo, 'accept', run['run'], 'launch', previous['launch'], '--reviewed-english', ok=False)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(load(run['decisions']), previous)
            self.assertNotEqual(publish_investigation(repo, run, ok=False).returncode, 0)
            self.assertEqual(invoke(repo, 'verify'), verified)
            answer['claims'][0]['evidence'][0]['end'] = 999
            save(shard, answer)
            self.assertNotEqual(invoke(repo, 'check-shard', run['run'], 'launch', ok=False).returncode, 0)

    def test_orientation_and_plan_revision_require_fresh_decisions(self):
        with test_directory() as repo:
            rev = fixture(repo, FILES)
            run = invoke(repo, 'investigate', '--commit', rev)
            self.assertEqual(load(run['plan'])['questions'], [])
            self.assertEqual(invoke(repo, 'read-input', run['run'], '@', 'package.json', '--count', '1')['lines'],
                             FILES['package.json'].splitlines())
            hit = invoke(repo, 'search-input', run['run'], 'cli.js', '--glob', 'scripts/*.ps1')
            self.assertIn('scripts/run.ps1', json.dumps(hit))
            self.assertNotEqual(publish_investigation(repo, run, ok=False).returncode, 0)

            add_question(run, 'launch', 'How does npm start the runner?', ['package.json'])
            add_question(run, 'report', 'How does the runner generate reports?', ['scripts/run.ps1'], ['launch'])
            entry = evidence(repo, run, 'launch', 'package.json', 1, 1)
            write_answer(run, 'launch', [invokes('npm:e2e', 'script:runner', entry)])
            guarded = evidence(repo, run, 'report', 'scripts/run.ps1', 2, 3)
            write_answer(run, 'report', [invokes('script:runner', 'command:allure-generate',
                                                guarded, condition=FRESH)])
            self.assertNotEqual(invoke(repo, 'check-shard', run['run'], 'report', ok=False).returncode, 0)
            accept(repo, run, 'launch')
            accept(repo, run, 'report')
            publish_investigation(repo, run)
            verified = invoke(repo, 'verify')

            plan = load(run['plan'])
            plan['questions'][0]['question'] = 'Which command starts the suite from npm?'
            save(run['plan'], plan)
            self.assertNotEqual(publish_investigation(repo, run, ok=False).returncode, 0)
            accept(repo, run, 'launch')
            self.assertNotEqual(publish_investigation(repo, run, ok=False).returncode, 0)
            self.assertEqual(invoke(repo, 'verify'), verified)
            accept(repo, run, 'report')
            publish_investigation(repo, run)
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

    def test_worktree_drift_preserves_previously_published_snapshot(self):
        with test_directory() as repo:
            rev = fixture(repo, FILES)
            previous, _ = start_launch(repo, '--commit', rev)
            publish_investigation(repo, previous)
            verified = invoke(repo, 'verify')
            run, _ = start_launch(repo, '--worktree')
            (repo / 'scripts/run.ps1').write_text('dotnet --version\n', encoding='utf-8')
            self.assertNotEqual(publish_investigation(repo, run, ok=False).returncode, 0)
            self.assertEqual(invoke(repo, 'verify'), verified)

    def test_missing_approval_preserves_existing_accepted_question(self):
        with test_directory() as repo:
            files = {name: source for name, source in FILES.items() if name != 'tools/verify.mjs'}
            rev = fixture(repo, files)
            first, _ = start_launch(repo, '--commit', rev)
            publish_investigation(repo, first)
            before = invoke(repo, 'verify')
            original = invoke(repo, 'trace', 'npm:e2e', '--type', 'invokes')

            repeat = invoke(repo, 'investigate', '--commit', rev)
            save(repeat['plan'], load(first['plan']))
            publish_investigation(repo, repeat, ok=False)
            self.assertEqual(invoke(repo, 'verify'), before)
            self.assertEqual(invoke(repo, 'trace', 'npm:e2e', '--type', 'invokes'), original)
