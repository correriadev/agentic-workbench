import copy, hashlib, json, pathlib, subprocess, tempfile
import sys

with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp) / 'payment'
    root.mkdir()
    def run(op, doc=None, destination=None, ok=True):
        cmd = [sys.executable, str(pathlib.Path(sys.argv[1]).resolve()), str(root), op]
        if destination:
            cmd += ['--expect', run('inspect')[destination] or 'absent']
        args = doc if isinstance(doc, str) else json.dumps(doc)
        r = subprocess.run(cmd, input=args, text=True, capture_output=True)
        assert (r.returncode == 0) == ok, (op, r.stderr)
        return json.loads(r.stdout) if op == 'inspect' else None

    def canonical(doc):
        return hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    run('scope', 'A1 one payment\nR1 duplicate\nR2 cache\n', 'scope_revision')
    scope = run('inspect')['scope_revision']
    checks = [dict(id=k, command='same-command', files=[k], qa_ids=[q]) for k, q in [('sql','QA-1'),('redis','QA-2')]]
    obligations = [
        dict(id=q, risk_ids=[risk], acceptance_ids=['A1'], blocking=True, status='ready', pending_reason=None,
             failure_to_detect='wrong count', preconditions=['setup'], stimulus='request',
             observables=['count'], assertions=['one'], environment='local', artifacts=['output'], source_refs=['repo'])
        for q, risk in [('QA-1','R1'),('QA-2','R2')]
    ]
    qa = dict(change_id='payment', scope_revision=scope, obligations=obligations, risk_coverage=[
        dict(risk_id=x['risk_ids'][0], obligation_ids=[x['id']]) for x in obligations])
    bad = copy.deepcopy(qa)
    del bad['obligations'][0]['observables']
    run('qa-plan', bad, 'qa_digest', False)
    run('qa-plan', qa, 'qa_digest')
    rev = run('inspect')['qa_revision']
    task = dict(id='T1', project_path=str(root), kind='evidence', status='pending',
                phase='evidence_pending', depends_on=[], evidence_checks=checks)
    plan = dict(change_id='payment', scope_revision=scope, qa_revision=rev, tasks=[task], evidence=[])
    run('plan', dict(plan, blocked_tasks=[{'id':'T1'}]), 'tasks_digest', False)
    run('plan', plan, 'tasks_digest')
    task['status'] = 'in_progress'
    run('build', plan, 'tasks_digest')
    for check, exit_code in zip(checks, [1, 0]):
        ident = check['id']
        definition = dict(cwd=str(root), check=check)
        result = dict(event='result', id=f'{ident}-result', attempt_id=f'{ident}-start', status='observed',
                      candidate_after='artifact', environment_after='compose-v1', artifact_ref='test-output',
                      observed_values={'rows':1 if not exit_code else 2}, exit_code=exit_code,
                      assertions=['one row'], test_refs=[ident])
        run('build', dict(plan, evidence=[*plan['evidence'], result]), 'tasks_digest', False)
        plan['evidence'].append(dict(event='started', id=result['attempt_id'], task_id='T1', check_id=ident,
                                    definition=definition, definition_digest=canonical(definition),
                                    qa_revision=rev, candidate='artifact', environment='compose-v1'))
        run('build', plan, 'tasks_digest')
        run('build', dict(plan, evidence=[*plan['evidence'], dict(result, environment_after='compose-v2')]), 'tasks_digest', False)
        plan['evidence'].append(result)
        run('build', plan, 'tasks_digest')
    task.update(status='failed',phase='failed')
    run('build', plan, 'tasks_digest')
    assessment = dict(id='gate',candidate='artifact',scope_revision=scope,qa_revision=rev,status='FAIL',findings=[
        dict(id='QA-1',status='FAIL',rationale='duplicate',evidence_ids=['sql-result']),
        dict(id='QA-2',status='PASS',rationale='one',evidence_ids=['redis-result']),
    ])
    run('qa-check', assessment, 'qa_digest')
    assert run('inspect')['qa_revision'] == rev
    changed = copy.deepcopy(plan)
    changed['tasks'][0]['evidence_checks'][0] = dict(checks[0], files=['replacement'])
    run('plan', changed, 'tasks_digest', False)
    changed['tasks'][0].update(status='pending',phase='evidence_pending')
    run('plan', changed, 'tasks_digest')
    run('qa-check', dict(assessment,id='stale-gate'), 'qa_digest', False)
    assert json.loads((root/'tasks.json').read_text())['evidence'] == plan['evidence']
    print('PASS: shape, DAG disjointness, prior start, environment drift, partial outcomes, QA result, replan and history')
