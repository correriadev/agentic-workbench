"""Plan, dispatch, admit evidence and account for every coverage assignment."""

from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import PurePosixPath
import re

from python_profile import MANIFEST, PROFILE, SUPPORTED, Source, extract, families, signal
from resolve import reconcile
from scan_files import MappingError, canonical, digest, linked


def area(path):
    return path.split('/', 1)[0] if '/' in path else '.'


def safe_path(root, relative, *, directory=False, create=False):
    path = root
    for part in PurePosixPath(relative).parts:
        if part in {'', '.', '..', '/'}:
            raise MappingError('invalid output path')
        path = path / part
        try:
            info = path.lstat()
        except FileNotFoundError:
            if create and path == root / relative:
                path.mkdir(exist_ok=True)
                info = path.lstat()
            else:
                continue
        if linked(info) or (not directory and path == root / relative and info.st_nlink != 1):
            raise MappingError(f'unsafe output path: {relative}')
        if path != root / relative or directory:
            if not path.is_dir():
                raise MappingError(f'output path must be a directory: {relative}')
        elif not path.is_file():
            raise MappingError(f'output path must be a regular file: {relative}')
    return path


def save(path, data):
    with path.open('x', encoding='utf-8', newline='\n') as output:
        output.write(canonical(data) + '\n')


def load(path):
    def unique(pairs):
        result = dict(pairs)
        if len(result) != len(pairs):
            raise MappingError('duplicate JSON object key')
        return result

    with path.open(encoding='utf-8') as source:
        return json.load(source, object_pairs_hook=unique)


def anchor_candidates(entries):
    def priority(path):
        name = PurePosixPath(path).name
        if path == MANIFEST:
            return 0
        if name in {'__main__.py', 'main.py', 'cli.py'}:
            return 1
        if signal(path):
            return 2
        return 3

    paths = [item['path'] for item in entries if item['eligible']]
    return sorted((path for path in paths if priority(path) < 3), key=lambda p: (priority(p), p))[:16]


def task(task_id, question, assigned, types, anchors, method, evidence, ambiguity, completion, dependencies=()):
    return dict(id=task_id, question=question, paths=assigned, types=list(types), anchors=anchors,
                method=method, evidence_required=evidence, likely_ambiguity=ambiguity,
                completion=completion, dependencies=list(dependencies), cross_links=['reconcile'],
                inputs=['inventory.json', 'plan.json', 'snapshot reader'],
                output=f'shards/{task_id}.json', status='planned')


def make_plan(manifest, reader, agent_review=False):
    entries = manifest['entries']
    by_area = defaultdict(list)
    supported_families = set(SUPPORTED)
    for entry in entries:
        by_area[area(entry['path'])].append(entry)
        supported_families.update(families(entry))
    anchors = []
    for path in anchor_candidates(entries):
        try:
            source = Source(reader, path)
            finding = dict(path=path, signals=signal(path), locator=source.anchor('plan-anchor'))
            if path == MANIFEST:
                parsed = extract(reader, path)
                facts = parsed['facts'] if parsed['kind'] == 'manifest' else {}
                finding.update(project_metadata=bool(facts.get('name')), declared_root=bool(facts.get('root')),
                               declared_entry_points=len(facts.get('scripts', [])),
                               declared_verification_roots=len(facts.get('tests', [])))
            anchors.append(finding)
        except (SyntaxError, UnicodeError, LookupError):
            anchors.append(dict(path=path, signals=signal(path), outcome='anchor text unavailable'))
    tasks, assignments = {}, []
    for location, group in sorted(by_area.items()):
        local_anchors = [anchor['path'] for anchor in anchors if area(anchor['path']) == location]
        baseline_id = 'scan-' + digest(location)[:16]
        assigned = [item['path'] for item in group if item['eligible'] and families(item)]
        if assigned:
            tasks[baseline_id] = task(
                baseline_id, 'Which supported relationships and architecture signals have source evidence?',
                assigned, sorted({kind for item in group for kind in families(item)}), local_anchors,
                ['AST/symbol table', 'TOML', 'targeted heading and path inspection'],
                'Every assigned input has a byte-bound result and every candidate has a locator.',
                'Unknown globals, resolver inputs, unsupported contracts and prose declarations.',
                'All assigned paths have validated outcomes.')
            tasks[baseline_id]['area'] = location
            if agent_review:
                review_id = 'review-' + digest(location)[:16]
                tasks[review_id] = task(
                    review_id, 'Which corroborated reference or declaration needs follow-up?', assigned,
                    tasks[baseline_id]['types'], local_anchors, ['targeted source inspection'],
                    'Each finding identifies a checked line and approved observation kind.',
                    'Source claims and agent assertions may disagree with static resolution.',
                    'Each assigned path is examined or remains visible as unexamined.', [baseline_id])
                tasks[review_id]['area'] = location
        for family in sorted(supported_families):
            relevant = [item for item in group if family in families(item)]
            eligible = [item['path'] for item in relevant if item['eligible']]
            basis = ('no profile input or recognized signal in inventory area' if not relevant
                     else 'declared profile construct' if family in SUPPORTED
                     else 'inventory signal; extraction unsupported')
            assignments.append(dict(area=location, family=family,
                                    paths=[item['path'] for item in relevant],
                                    task=baseline_id if eligible else None,
                                    method=(tasks[baseline_id]['method'] if family in SUPPORTED else
                                            ['targeted signal inspection']) if eligible else [],
                                    basis=basis))
        if agent_review and assigned:
            assignments.append(dict(area=location, family='agent-review', paths=assigned, task=review_id,
                                    method=['targeted source inspection'], basis='requested supplemental review'))
    baseline = [key for key in tasks if key.startswith('scan-')]
    tasks['reconcile'] = task('reconcile', 'Which candidates bind across areas under the recorded profile?',
                              [], SUPPORTED, [a['path'] for a in anchors], ['global namespace indexes'],
                              'Cross-area endpoints and resolver inputs support each resolved relationship.',
                              'Multiple candidates or unobserved runtime namespace changes.',
                              'Resolve or retain every candidate with its outcome.', baseline)
    tasks['reconcile']['cross_links'] = ['frontier']
    tasks['frontier'] = task('frontier', 'What evidence would reduce the unresolved frontier?',
                             [], sorted(supported_families), [], ['coverage audit'],
                             'Every incomplete assignment has a reason and a task or path to revisit.',
                             'Future language or runtime evidence may be needed.',
                             'Retain all incomplete assignments and their follow-up.', ['reconcile'])
    tasks['frontier']['cross_links'] = []
    themes = {
        'source-build': ('structural', 'membership', 'other-language', 'architecture-declaration'),
        'runtime-deployment': ('semantic', 'runtime-deployment'),
        'interfaces-contracts': ('interfaces', 'event-contract'),
        'data': ('data-ownership',),
        'verification': ('verification',),
        'supplemental': ('agent-review',),
    }
    workstreams = []
    for name, kinds in themes.items():
        pairs = [entry for entry in assignments if entry['paths'] and entry['family'] in kinds]
        if pairs:
            workstreams.append(dict(id=name, tasks=sorted({entry['task'] for entry in pairs if entry['task']}),
                                    assignments=[[entry['area'], entry['family']] for entry in pairs]))
    plan = dict(snapshot=manifest['snapshot']['identity'], profile=PROFILE, anchors=anchors, tasks=tasks,
                workstreams=workstreams, coverage=assignments, agent_review=agent_review)
    plan['id'] = digest(plan)
    return plan


def envelope(plan, key, *, outcomes=None, status='completed', reason=''):
    assigned = plan['tasks'][key]['paths']
    return dict(plan=plan['id'], task=key, snapshot=plan['snapshot'], status=status, reason=reason,
                inputs=assigned if status == 'completed' else [], outcomes=outcomes or {})


def baseline_task(plan, key, reader):
    for attempt in range(2):
        try:
            return envelope(plan, key, outcomes={path: extract(reader, path)
                                                for path in plan['tasks'][key]['paths']})
        except TimeoutError:
            if attempt:
                return envelope(plan, key, status='blocked', reason='local extraction timed out twice')
    raise AssertionError('extraction attempts')


def collect(plan, reader, stage):
    keys = [key for key in plan['tasks'] if key.startswith('scan-')]
    if not keys:
        return
    with ThreadPoolExecutor(max_workers=min(4, len(keys))) as pool:
        futures = {key: pool.submit(baseline_task, plan, key, reader) for key in keys}
        for key, future in futures.items():
            save(safe_path(stage, plan['tasks'][key]['output']), future.result())


def validate_baseline(plan, key, shard, reader):
    if shard.get('status') == 'blocked':
        blocked = envelope(plan, key, status='blocked', reason='local extraction timed out twice')
        if shard != blocked:
            raise MappingError(f'invalid blocked shard: {key}')
        return {path: dict(status='blocked', kind='blocked', reason=blocked['reason'], facts=[])
                for path in plan['tasks'][key]['paths']}
    # Reparse through the same snapshot reader. A claimed locator or binding alone cannot enter the graph.
    expected = baseline_task(plan, key, reader)
    if shard != expected:
        raise MappingError(f'shard does not reproduce from snapshot: {key}')
    return shard['outcomes']


REVIEW_TERMS = {
    'runtime-deployment': r'\b(deploy(?:ment|ed)?|runtime|container)\b',
    'event-contract': r'\b(asyncapi|channel|message|send|receive)\b',
    'interfaces': r'\b(openapi|endpoint|interface)\b',
    'data-ownership': r'\b(database|storage|schema|ownership)\b',
    'verification': r'\b(test(?:s|ing)?|verification)\b',
    'architecture-declaration': r'\b(architecture|component|module|boundary)\b',
}


def review_envelope(plan, key, data, reader):
    if not isinstance(data, dict) or set(data) != {'plan', 'task', 'snapshot', 'status', 'inputs', 'findings'}:
        raise MappingError('invalid review schema')
    task_record = plan['tasks'][key]
    assigned = task_record['paths']
    inputs = data['inputs']
    if (data['plan'], data['task'], data['snapshot']) != (plan['id'], key, plan['snapshot']):
        raise MappingError('review task or snapshot mismatch')
    if (data['status'] not in {'completed', 'partial', 'blocked'} or not isinstance(inputs, list)
            or not all(isinstance(path, str) and path in assigned for path in inputs)
            or len(set(inputs)) != len(inputs) or not isinstance(data['findings'], list)
            or (data['status'] == 'completed' and set(inputs) != set(assigned))):
        raise MappingError('invalid review coverage')
    normalized = {}
    for fact in data['findings']:
        if not isinstance(fact, dict) or set(fact) != {'path', 'content_id', 'line', 'kind'}:
            raise MappingError('invalid review finding')
        path, kind, line = fact['path'], fact['kind'], fact['line']
        if (path not in inputs or not isinstance(kind, str) or kind not in REVIEW_TERMS or type(line) is not int
                or fact['content_id'] != reader.entries[path]['content_id']):
            raise MappingError('review finding is outside its input or has an invalid identity')
        source = Source(reader, path)
        if not 1 <= line <= len(source.lines) or not re.search(REVIEW_TERMS[kind], source.lines[line - 1].decode(), re.I):
            raise MappingError('review anchor does not substantiate a candidate signal')
        observation = source.anchor('review-signal', kind, line=line)
        normalized[digest(observation)] = observation
    return dict(task=key, status=data['status'], inputs=sorted(inputs),
                observations=[normalized[key] for key in sorted(normalized)])


def reviews(plan, stage, reader):
    output = {}
    for key, task_record in plan['tasks'].items():
        if not key.startswith('review-'):
            continue
        path = safe_path(stage, task_record['output'])
        if not path.exists():
            output[key] = dict(task=key, status='unexamined', inputs=[], observations=[])
            continue
        try:
            output[key] = review_envelope(plan, key, load(path), reader)
        except (ValueError, TypeError, KeyError, SyntaxError, LookupError, MappingError) as error:
            if 'snapshot' in str(error) and str(error).startswith('snapshot'):
                raise
            output[key] = dict(task=key, status='blocked', inputs=[], observations=[],
                               reason='supplemental shard failed validation')
    return output


def project(baseline, supplemental):
    graph = reconcile(baseline)
    for shard in supplemental.values():
        for anchor in shard['observations']:
            ev = graph.observe(anchor, 'review-source-signal', 'candidate', 'unresolved declaration or boundary')
            graph.discrepancy('supplemental-signal', anchor['path'],
                              'corroborate the signal before assigning a typed relationship', [ev])
    return graph


def final_coverage(plan, inventory, outcomes, graph, supplemental):
    entries = {entry['path']: entry for entry in inventory['entries']}
    paths_by_node = defaultdict(set)
    origin_bases = {'module-source', 'function-definition', 'project-metadata',
                    'console-script-declaration', 'source-file'}
    for node, evidence in graph.node_observations:
        observation = graph.observations[evidence]
        if observation['basis'] in origin_bases:
            paths_by_node[node].add(graph.occurrences[observation['occurrence']]['path'])
    hits = Counter()
    for edge in graph.relationships.values():
        for path in paths_by_node[edge['source']]:
            hits[path, edge['family']] += 1
    for _, _, node in graph.memberships:
        for path in paths_by_node[node]:
            hits[path, 'membership'] += 1
    records = []
    for assignment in plan['coverage']:
        family, key = assignment['family'], assignment['task']
        paths = assignment['paths']
        record = dict(assignment, status='analyzed', reason='all assigned constructs examined', scoped_absence=False,
                      findings=sum(hits[path, family] for path in paths), issues=[])
        if family == 'agent-review':
            shard = supplemental[key]
            record['status'] = 'analyzed' if shard['status'] == 'completed' else shard['status']
            record['findings'] = len(shard['observations'])
            record['reason'] = shard.get('reason', 'supplemental review ' + shard['status'])
        elif not paths:
            record.update(status='inapplicable', reason=assignment['basis'])
        else:
            statuses = set()
            for path in paths:
                entry = entries[path]
                if entry['status'] != 'pending':
                    state = 'excluded' if entry['status'] in {'excluded', 'deleted'} else entry['status']
                    reason = entry['reason']
                elif outcomes[path]['status'] in {'blocked', 'partial'}:
                    state, reason = outcomes[path]['status'], outcomes[path]['reason']
                elif family not in SUPPORTED:
                    state, reason = 'unsupported', 'signal found outside active profile'
                elif issues := graph.issues.get((path, family)):
                    state, reason = 'partial', '; '.join(sorted(issues))
                else:
                    state, reason = 'analyzed', ''
                statuses.add(state)
                if reason:
                    record['issues'].append(dict(path=path, status=state, reason=reason))
            record['status'] = next(iter(statuses)) if len(statuses) == 1 else (
                'analyzed' if statuses == {'analyzed', 'excluded'} else 'partial')
            if record['status'] != 'analyzed':
                record['reason'] = record['issues'][0]['reason']
            record['scoped_absence'] = record['status'] == 'analyzed' and record['findings'] == 0
        records.append(record)
    return records
