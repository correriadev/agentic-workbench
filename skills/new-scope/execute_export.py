"""Project a New Scope revision into the existing Execute Scope task contract."""
import hashlib
import json
from pathlib import Path

from completeness import Plan, assess, repository_path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_json(path):
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Unsafe {path.name}')
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError(f'{path.name} must be an object')
    return value


def export_execute_scope(db, folder, metadata, scope_bytes):
    source = folder / 'context.sqlite'
    if any((folder / ('context.sqlite' + suffix)).exists() for suffix in ('-wal', '-journal')):
        raise ValueError('Close active New Scope writers before exporting')
    source_hash = sha(source.read_bytes())
    scope_hash = sha(scope_bytes)
    qa = load_json(folder / 'qa.json')
    contract = qa.get('contract') if qa else None
    if qa and (not isinstance(contract, dict) or contract.get('change_id') != metadata['change_id']
               or contract.get('scope_revision') != scope_hash):
        raise ValueError('QA contract is stale or incompatible with this scope')
    qa_revision = sha(json.dumps(contract, sort_keys=True, ensure_ascii=True,
                                 separators=(',', ':'), allow_nan=False).encode()) if contract else None
    obligations = {item['id']: item for item in contract.get('obligations', [])} if contract else {}
    if contract and len(obligations) != len(contract.get('obligations', [])):
        raise ValueError('QA contract has duplicate obligations')

    graph = Plan(db)
    report = assess(db)
    tasks = {}
    reasons = {key: [] for key in graph.kinds['task']}
    global_gaps = [item['message'] for item in report['gaps'] if item['node'] == 'spec']
    for key in report['blocked_tasks']:
        reasons[key].extend(item['message'] for item in report['gaps'] if item['node'] == key)
    for key in sorted(reasons):
        reasons[key].extend(global_gaps)
        node = graph.nodes[key]
        detail = db.execute('SELECT * FROM task_details WHERE task_id=?', (key,)).fetchone()
        if not detail:
            continue
        files = [dict(row) for row in db.execute('SELECT * FROM task_files WHERE task_id=? ORDER BY path', (key,))]
        allowed = [item['path'] for item in files]
        units = [item['path'] for item in files if item['role'] == 'unit']
        if detail['kind'] == 'implementation' and not any(item['role'] == 'production' for item in files):
            reasons[key].append('Implementation requires an authorized production file.')
        if detail['kind'] == 'evidence' and any(item['role'] == 'production' for item in files):
            reasons[key].append('Evidence tasks cannot authorize production files.')
        for file in files:
            current = Path(detail['project_root'])
            for part in Path(file['path']).parts:
                current = current / part
                if current.is_symlink():
                    reasons[key].append('Task path contains a symlink: ' + file['path'])
                    break
        details = node['details']
        checks = details.get('evidence_checks', [])
        qa_ids = details.get('qa_ids', [])
        valid_texts = lambda value: isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value)
        if not valid_texts(qa_ids) or not isinstance(checks, list):
            reasons[key].append('QA identifiers and evidence checks must be arrays.')
            qa_ids, checks = [], []
        seen = set()
        for check in checks:
            if (not isinstance(check, dict) or not isinstance(check.get('id'), str) or not check['id'].strip()
                    or check['id'] in seen or not isinstance(check.get('command'), str)
                    or not check['command'].strip() or not valid_texts(check.get('qa_ids'))
                    or not check['qa_ids'] or not valid_texts(check.get('files', []))):
                reasons[key].append('Evidence check lacks an ID, command, valid file references, or QA links.')
                continue
            try:
                for path in check.get('files', []):
                    repository_path(detail['project_root'], path)
            except (OSError, ValueError):
                reasons[key].append('Evidence check has an invalid project-relative file reference.')
            seen.add(check['id'])
            qa_ids = list(dict.fromkeys([*qa_ids, *check['qa_ids']]))
        if detail['kind'] == 'evidence' and (not checks or not qa_ids):
            reasons[key].append('Evidence tasks require explicitly mapped QA checks and obligations.')
        if any(q not in obligations or obligations[q].get('status') != 'ready' for q in qa_ids):
            reasons[key].append('QA obligations are absent or pending.')
        item = dict(id=key, kind=detail['kind'], project_path=detail['project_root'],
                    description=node['content'], technical_steps=[node['content']],
                    acceptance_ids=graph.linked(key, 'implements', 'acceptance'),
                    files_allowed=allowed, planned_files=[item['path'] for item in files if item['origin'] == 'new'],
                    depends_on=[dict(task=dep) for dep in graph.linked(key, 'depends_on', 'task')],
                    status='pending', phase='red_pending' if detail['kind'] == 'implementation' else 'evidence_pending',
                    qa_ids=qa_ids, evidence_checks=checks)
        if detail['kind'] == 'implementation':
            item.update(unit_tests=dict(files=units, command=detail['unit_command']),
                        red=detail['red'], green=detail['green'])
        if details.get('smoke_command'):
            item['smoke_command'] = details['smoke_command']
        tasks[key] = item

    while True:
        blocked = {key for key, messages in reasons.items() if messages}
        changed = False
        for key, task in tasks.items():
            if key not in blocked and any(dep['task'] in blocked for dep in task['depends_on']):
                reasons[key].append('A prerequisite task is blocked.')
                changed = True
        if not changed:
            break
    prior = load_json(folder / 'tasks.json')
    evidence = prior.get('evidence', []) if prior else []
    if not isinstance(evidence, list):
        raise ValueError('Prior task evidence must be an array')
    if sha(source.read_bytes()) != source_hash:
        raise ValueError('New Scope changed during export; retry')
    return dict(change_id=metadata['change_id'], scope_revision=scope_hash, qa_revision=qa_revision,
                blueprint_source=dict(revision=metadata['revision'], sha256=source_hash),
                tasks=[tasks[key] for key in sorted(tasks) if not reasons[key]],
                blocked_tasks=[dict(id=key, reason=' '.join(reasons[key])) for key in sorted(reasons) if reasons[key]],
                evidence=evidence)
