"""Exercise the specification-to-execution contract with real SQLite and CLI processes."""
import hashlib
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PLANNER = Path(__file__).resolve().parents[1] / 'contract.py'
EXECUTOR = Path(__file__).resolve().parents[2] / 'execute-scope/contract.py'
QUALITY = Path(__file__).resolve().parents[2] / 'qa-scope/contract.py'
MAPPER = Path(__file__).resolve().parents[2] / 'project-mapper/scripts/project_mapper.py'


def node(key, kind, content, state='planned', origin='inference', **details):
    return dict(id=key, kind=kind, title=key, content=content, state=state,
                origin=origin, details=details)


class ScopeHandoff(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.folder = self.root / 'docs/specs/example'
        (self.root / 'tests').mkdir()
        runner = self.root / 'tests/test_existing.py'
        runner.write_text('import unittest\n', encoding='utf-8')
        self.bp('init')
        self.plan = dict(
            request_id='initial', reason='Describe one behavior',
            nodes=[node('I1', 'intent', 'Allow the operation.', 'confirmed', 'human'),
                   node('A1', 'acceptance', 'The operation succeeds.'),
                   node('B1', 'behavior', 'Return the result.'),
                   node('T1', 'task', 'Implement the behavior.'),
                   node('S1', 'test_scenario', 'Test the operation.'),
                   node('AS1', 'assertion', 'Check the result.', observables=['result'])],
            sources=[dict(id='SRC1', project_root=str(self.root), path='tests/test_existing.py',
                          sha256=hashlib.sha256(runner.read_bytes()).hexdigest())],
            edges=[dict(src=a, relation=b, dst=c, rationale='Ground the task.') for a, b, c in [
                ('A1', 'requires', 'B1'), ('B1', 'verified_by', 'S1'),
                ('T1', 'implements', 'A1'), ('T1', 'verified_by', 'S1'),
                ('S1', 'has_assertion', 'AS1')]],
            task_details=[dict(task_id='T1', project_root=str(self.root), kind='implementation',
                               unit_command='python -m unittest tests.test_new', runner_source='SRC1',
                               red='The result is missing.', green='The result is returned.')],
            task_files=[dict(task_id='T1', path='tests/test_new.py', origin='new', role='unit'),
                        dict(task_id='T1', path='app.py', origin='new', role='production')],
            verification_cases=[dict(scenario_id='S1', level='unit', conditions='Configured input.',
                                     steps='Run the operation.', expected='Return the result.',
                                     command='python -m unittest tests.test_new')])

    def call(self, cli, operation, *args, payload=None, ok=True):
        result = subprocess.run([sys.executable, str(cli), str(self.folder), operation, *args],
                                input=json.dumps(payload) if payload is not None else None,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, ok, result.stderr or result.stdout)
        return json.loads(result.stdout) if result.stdout else result.stderr

    def bp(self, operation, *args, **kwargs):
        return self.call(PLANNER, operation, *args, **kwargs)

    def executor(self, operation, *args, **kwargs):
        return self.call(EXECUTOR, operation, *args, **kwargs)

    def publish(self):
        self.bp('apply', '--expect', '0', payload=self.plan)
        self.bp('render-scope')
        return self.bp('export-forge')

    def test_new_export_name_keeps_legacy_projection_compatible(self):
        legacy = self.publish()
        self.assertEqual(self.bp('export-execute-scope'), legacy)

    def test_ready_plan_becomes_a_version_bound_forge_contract(self):
        plan = self.publish()
        self.assertEqual(plan['blueprint_source']['revision'], 1)
        self.assertEqual(plan['tasks'][0]['files_allowed'], ['app.py', 'tests/test_new.py'])
        self.assertEqual(plan['tasks'][0]['unit_tests']['files'], ['tests/test_new.py'])
        self.assertEqual(plan['tasks'][0]['phase'], 'red_pending')
        self.executor('plan', '--expect', 'absent', payload=plan)
        plan['tasks'][0]['status'] = 'in_progress'
        self.executor('build', '--expect', self.executor('inspect')['tasks_digest'], payload=plan)
        self.bp('apply', '--expect', '1', payload=dict(request_id='revision', reason='New decision',
                nodes=[node('D1', 'decision', 'New decision.', 'confirmed', 'human')]))
        result = self.executor('build', '--expect', self.executor('inspect')['tasks_digest'],
                            payload=plan, ok=False)
        self.assertIn('New Scope', result)

    def test_missing_production_file_blocks_task_and_dependents(self):
        self.plan['task_files'].pop()
        self.plan['nodes'].append(node('T2', 'task', 'Dependent implementation.'))
        self.plan['task_details'].append(dict(self.plan['task_details'][0], task_id='T2'))
        self.plan['task_files'].extend([dict(task_id='T2', path='tests/test_other.py', origin='new', role='unit'),
                                        dict(task_id='T2', path='other.py', origin='new', role='production')])
        self.plan['edges'].extend([dict(src='T2', relation='depends_on', dst='T1', rationale='Prerequisite.'),
                                   dict(src='T2', relation='implements', dst='A1', rationale='Same behavior.'),
                                   dict(src='T2', relation='verified_by', dst='S1', rationale='Same command.')])
        plan = self.publish()
        self.assertEqual(plan['tasks'], [])
        self.assertEqual([item['id'] for item in plan['blocked_tasks']], ['T1', 'T2'])
        self.executor('plan', '--expect', 'absent', payload=plan)

    def test_plan_cannot_add_files_or_change_tests_after_export(self):
        plan = self.publish()
        forged = copy.deepcopy(plan)
        forged['tasks'][0]['files_allowed'].append('unplanned.py')
        self.assertIn('New Scope', self.executor('plan', '--expect', 'absent', payload=forged, ok=False))
        forged = copy.deepcopy(plan)
        forged['tasks'][0]['unit_tests']['command'] = 'python -m unittest all_tests'
        self.assertIn('New Scope', self.executor('plan', '--expect', 'absent', payload=forged, ok=False))

    def test_changed_scope_must_be_rendered_before_export(self):
        self.publish()
        (self.folder / 'SCOPE.md').write_text('edited', encoding='utf-8')
        self.assertIn('scope', self.bp('export-forge', ok=False).lower())

    def test_quality_gate_cannot_overwrite_a_blueprint_scope(self):
        self.publish()
        current = self.executor('inspect')['scope_revision']
        self.assertIn('New Scope', self.call(QUALITY, 'scope', '--expect', current,
                                            payload='different scope', ok=False))

    def test_real_project_map_reference_survives_handoff(self):
        def git(*args):
            subprocess.run(['git', '-C', str(self.root), *args], capture_output=True, text=True, check=True)

        git('init', '-q')
        git('add', 'tests/test_existing.py')
        git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test',
            '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')
        subprocess.run([sys.executable, str(MAPPER), str(self.root), 'map', '--commit', 'HEAD'],
                       capture_output=True, text=True, check=True)
        result = subprocess.run([sys.executable, str(MAPPER), str(self.root), '--offline',
                                 'node', 'file:tests/test_existing.py'],
                                capture_output=True, text=True, check=True)
        mapped = json.loads(result.stdout)
        locator = mapped['nodes'][0]['evidence'][0]
        source = self.bp('source-ref', 'SRC1', '--path', locator['path'],
                         '--lines', str(locator['span'][0]), str(locator['span'][2]),
                         '--expect-content-id', locator['content_id'])
        self.plan['sources'] = [source]
        behavior = next(n for n in self.plan['nodes'] if n['id'] == 'B1')
        behavior['details']['project_mapper'] = dict(
            graph_sha256=mapped['graph_identity']['sha256'], snapshot=mapped['graph_identity']['snapshot'],
            node='file:tests/test_existing.py', limitations='Static source candidate.')
        self.plan['node_sources'] = [dict(node_id='B1', source_id='SRC1')]
        exported = self.publish()
        self.executor('plan', '--expect', 'absent', payload=exported)
        observed = self.bp('get', 'B1')
        self.assertEqual(observed['details']['project_mapper']['graph_sha256'], mapped['graph_identity']['sha256'])
        self.assertEqual(observed['sources'][0]['path'], 'tests/test_existing.py')
        self.assertEqual(observed['sources'][0]['version'], locator['content_id'])

        (self.root / locator['path']).write_text('import unittest\n\n# Changed after mapping.\n', encoding='utf-8')
        stale = self.bp('source-ref', 'SRC2', '--path', locator['path'],
                        '--expect-content-id', locator['content_id'], ok=False)
        self.assertIn('Source content changed', stale)

    def test_explicit_qa_mapping_flows_to_gate_and_stale_plan_is_rejected(self):
        # A check may read an existing test outside the task's write allowlist.
        check = dict(id='check', command='python -c "print(1)"', files=['tests/test_existing.py'], qa_ids=['QA-1'])
        task = next(n for n in self.plan['nodes'] if n['id'] == 'T1')
        task['details'] = dict(qa_ids=['QA-1'], evidence_checks=[check])
        self.plan['nodes'].extend([node('R1', 'risk', 'Wrong result.', 'applicable', 'catalog'),
                                   node('O1', 'verification_obligation', 'Check result.',
                                        observables=['result'], artifacts=['output'])])
        self.plan['edges'].extend([dict(src=a, relation=b, dst=c, rationale='Verify the risk.') for a, b, c in [
            ('R1', 'requires', 'O1'), ('O1', 'verified_by', 'S1')]])
        self.bp('apply', '--expect', '0', payload=self.plan)
        self.bp('render-scope')
        scope = hashlib.sha256((self.folder / 'SCOPE.md').read_bytes()).hexdigest()
        qa = dict(change_id='example', scope_revision=scope, risk_coverage=[dict(risk_id='R1', obligation_ids=['QA-1'])],
                  obligations=[dict(id='QA-1', risk_ids=['R1'], acceptance_ids=['A1'], blocking=True,
                                    status='ready', pending_reason=None, failure_to_detect='Wrong result.',
                                    preconditions=['Input exists.'], stimulus='Run check.', observables=['result'],
                                    assertions=['One result.'], environment='local', artifacts=['output'], source_refs=['SRC1'])])
        self.call(QUALITY, 'qa-plan', '--expect', 'absent', payload=qa)
        plan = self.bp('export-forge')
        self.assertEqual(plan['tasks'][0]['evidence_checks'], [check])
        self.executor('plan', '--expect', 'absent', payload=plan)

        def update():
            self.executor('build', '--expect', self.executor('inspect')['tasks_digest'], payload=plan)

        plan['tasks'][0]['status'] = 'in_progress'
        update()
        plan['tasks'][0]['phase'] = 'green_pending'
        update()
        plan['tasks'][0].update(status='completed', phase='completed')
        update()
        definition = dict(cwd=str(self.root), check=check)
        definition_digest = hashlib.sha256(json.dumps(definition, sort_keys=True, ensure_ascii=True,
                    separators=(',', ':')).encode()).hexdigest()
        plan['evidence'].append(dict(event='started', id='start', task_id='T1', check_id='check',
                         definition=definition, definition_digest=definition_digest,
                         qa_revision=plan['qa_revision'], candidate='candidate', environment='local'))
        update()
        observed = subprocess.run([sys.executable, '-c', 'print(1)'], capture_output=True, text=True, check=True)
        plan['evidence'].append(dict(event='result', id='result', attempt_id='start', status='observed',
                         candidate_after='candidate', environment_after='local', artifact_ref='output',
                         observed_values={'result': observed.stdout.strip()}, exit_code=observed.returncode,
                         assertions=['One result.'], test_refs=['tests/test_new.py']))
        update()
        assessment = dict(id='gate', candidate='candidate', scope_revision=scope, qa_revision=plan['qa_revision'],
                          status='PASS', findings=[dict(id='QA-1', status='PASS', rationale='Result observed.',
                                                       evidence_ids=['result'])])
        self.call(QUALITY, 'qa-check', '--expect', self.executor('inspect')['qa_digest'], payload=assessment)
        self.bp('apply', '--expect', '1', payload=dict(request_id='revision', reason='New decision',
                nodes=[node('D1', 'decision', 'New decision.', 'confirmed', 'human')]))
        assessment['id'] = 'stale'
        self.assertIn('New Scope', self.call(QUALITY, 'qa-check', '--expect', self.executor('inspect')['qa_digest'],
                                            payload=assessment, ok=False))


if __name__ == '__main__':
    unittest.main()
