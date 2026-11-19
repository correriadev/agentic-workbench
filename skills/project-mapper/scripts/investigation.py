"""Validate a supervisor's investigation plan and compile accepted source claims."""

from functools import lru_cache, partial
from graphlib import CycleError, TopologicalSorter
import hashlib
import re

import graph_store
from python_profile import Source
from resolve import Graph
from scan_files import MappingError, canonical


SLUG = re.compile(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*')
DEVICE = re.compile(r'con|prn|aux|nul|com[1-9]|lpt[1-9]')


def new_plan(identity):
    return {'snapshot': identity, 'questions': []}


def fields(obj, keys, name):
    if not isinstance(obj, dict) or set(obj) != set(keys.split()):
        raise MappingError(f'invalid {name} fields: expected {keys}')


def string(value, name, *, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()) or value != value.strip():
        raise MappingError(f'invalid or empty {name}')
    if value and not value.isprintable():
        raise MappingError(f'{name} must be one printable line')
    return value


def slug(value, name):
    if not isinstance(value, str) or not SLUG.fullmatch(value):
        raise MappingError(f'{name} must be a lowercase slug')
    return value


def string_list(value, name):
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise MappingError(f'invalid {name} list')
    if len(set(value)) != len(value):
        raise MappingError(f'duplicate entry in {name}')
    return value


def validate_plan(plan, identity, entries):
    fields(plan, 'snapshot questions', 'investigation plan')
    if plan['snapshot'] != identity or not isinstance(plan['questions'], list):
        raise MappingError('plan requires the current inventory snapshot and a question list')
    eligible = {entry['path'] for entry in entries if entry['eligible']}
    dependencies = {}
    for item in plan['questions']:
        fields(item, 'id question seeds depends_on', 'question')
        key = slug(item['id'], 'question id')
        if len(key) > 128 or DEVICE.fullmatch(key) or key in dependencies:
            raise MappingError(f'duplicate or unusable question id: {key}')
        string(item['question'], 'question')
        seeds = string_list(item['seeds'], 'seeds')
        if set(seeds) - eligible:
            raise MappingError(f'question {key} has seed paths outside the eligible snapshot')
        dependencies[key] = string_list(item['depends_on'], 'depends_on')
    if any(set(deps) - dependencies.keys() for deps in dependencies.values()):
        raise MappingError('plan references an unknown dependency')
    try:
        TopologicalSorter(dependencies).prepare()
    except CycleError as error:
        raise MappingError('plan has a dependency cycle') from error
    return plan


def endpoint(value, entries):
    string(value, 'endpoint')
    kind, sep, name = value.partition(':')
    if not sep or not name.strip() or name != name.strip():
        raise MappingError('endpoint must be a typed key (kind:name)')
    slug(kind, 'endpoint kind')
    if kind == 'file' and (name not in entries or not entries[name]['eligible']):
        raise MappingError(f'file endpoint outside the eligible snapshot: {name}')


def evidence_text(reader, path):
    source = Source(reader, path)
    if '\x00' in source.text:
        raise MappingError(f'cannot use binary content as text evidence: {path}')
    return source


def source_anchor(ref, question, reader, read_source):
    fields(ref, 'path content_id start end', 'evidence')
    path = ref['path']
    entry = reader.entries.get(path) if isinstance(path, str) else None
    if not entry or not entry['eligible'] or ref['content_id'] != entry['content_id']:
        raise MappingError(f'evidence path or content identity differs from the snapshot: {path}')
    start, end = ref['start'], ref['end']
    if type(start) is not int or type(end) is not int or not 1 <= start <= end:
        raise MappingError(f'invalid evidence line range: {path}')
    try:
        source = read_source(path)
    except (UnicodeError, SyntaxError, LookupError) as error:
        raise MappingError(f'cannot decode source evidence: {path}') from error
    if end > len(source.lines):
        raise MappingError(f'evidence range extends past end of file: {path}')
    span = [start, 0, end, len(source.lines[end - 1])]
    excerpt = source.excerpt(span)
    if not excerpt.strip():
        raise MappingError(f'evidence must cite nonempty source lines: {path}')
    return dict(path=path, content_id=entry['content_id'], span=span, kind='source-range',
                symbol=question, excerpt_digest=hashlib.sha256(excerpt).hexdigest())


def evidence_ranges(refs, question, reader, read_source):
    if not isinstance(refs, list) or not refs:
        raise MappingError('each finding requires a source locator')
    return [source_anchor(ref, question, reader, read_source) for ref in refs]


def checked_findings(question_id, raw, manifest, reader, read_source):
    has_absence = isinstance(raw, dict) and 'absence' in raw
    fields(raw, 'snapshot question status claims gap' + (' absence' if has_absence else ''), 'investigation shard')
    if raw['snapshot'] != manifest['snapshot']['identity'] or raw['question'] != question_id:
        raise MappingError('shard question or snapshot mismatch')
    status, claims, gap = raw['status'], raw['claims'], raw['gap']
    if status not in ('answered', 'partial', 'blocked') or not isinstance(claims, list):
        raise MappingError('invalid shard status or claims')
    string(gap, 'evidence gap', empty=True)
    if has_absence and (status != 'answered' or claims):
        raise MappingError('a scoped absence requires an answered question with zero positive claims')
    if status == 'answered' and (not claims and not has_absence or gap):
        raise MappingError('an answered question requires an evidenced relationship or scoped absence and no gap')
    if status != 'answered' and not gap:
        raise MappingError('a partial or blocked question requires a concrete gap')
    if status == 'blocked' and claims:
        raise MappingError('use partial for a question with both supported claims and a gap')

    checked = []
    for claim in claims:
        fields(claim, 'source relation target condition evidence', 'claim')
        endpoint(claim['source'], reader.entries)
        endpoint(claim['target'], reader.entries)
        slug(claim['relation'], 'relation')
        string(claim['condition'], 'condition', empty=True)
        checked.append((claim, evidence_ranges(claim['evidence'], question_id, reader, read_source)))
    absence_anchors = []
    if has_absence:
        absence = raw['absence']
        fields(absence, 'statement evidence', 'scoped absence')
        string(absence['statement'], 'scoped absence statement')
        absence_anchors = evidence_ranges(absence['evidence'], question_id, reader, read_source)
    return checked, absence_anchors


def validate_shard(question_id, raw, manifest, reader):
    """Check the envelope, endpoints and cited bytes. The supervisor assesses meaning."""
    read_source = lru_cache(maxsize=8)(partial(evidence_text, reader))
    checked_findings(question_id, raw, manifest, reader, read_source)
    return raw


def compile_investigation(manifest, plan, shards, reader):
    """Rebuild logical rows from the accepted subset, retaining every planned question."""
    validate_plan(plan, manifest['snapshot']['identity'], manifest['entries'])
    questions = {item['id']: item for item in plan['questions']}
    if not isinstance(shards, dict) or shards.keys() - questions.keys():
        raise MappingError('accepted shards must belong to the investigation plan')
    read_source = lru_cache(maxsize=8)(partial(evidence_text, reader))
    checked = {key: checked_findings(key, raw, manifest, reader, read_source) for key, raw in shards.items()}
    relations = sorted({claim['relation'] for claims, _ in checked.values() for claim, _ in claims})
    profile = dict(name='agent-investigation', version=1, edge_types={'semantic': relations, 'structural': []})
    graph = Graph(profile=profile)
    coverage, reports, outcomes = [], {}, {}
    for key, question in questions.items():
        shard = shards.get(key)
        status = shard['status'] if shard else 'unexamined'
        gap = shard['gap'] if shard else 'No supervisor-accepted answer for this question.'
        claims, absence_anchors = checked.get(key, ([], []))
        cited = {anchor['path'] for anchor in absence_anchors}
        reason = gap or 'Planned question answered with supervisor-reviewed source claims.'
        if absence_anchors:
            reason = shard['absence']['statement']
            sources = [graph.observe(anchor, 'agent-scoped-absence', 'source', 'Absence scoped to the question.')
                       for anchor in absence_anchors]
            graph.discrepancy('scoped-absence', absence_anchors[0]['path'], reason, sources)
        for claim, anchors in claims:
            limitation = 'Supervisor-reviewed static claim; verification replays source locators.'
            if claim['condition']:
                limitation += ' Condition: ' + claim['condition']
            evidence = [graph.observe(anchor, 'agent-source-reading', 'source', limitation) for anchor in anchors]
            cited.update(anchor['path'] for anchor in anchors)
            for node in (claim['source'], claim['target']):
                kind, name = node.split(':', 1)
                graph.node(node, kind, 'investigation', name, evidence)
            graph.relation(claim['relation'], claim['source'], claim['target'], 'resolved', evidence,
                           conditions=[claim['condition']] if claim['condition'] else [])
            if claim['relation'] == 'member-of':
                dimension = claim['target'].partition(':')[0]
                graph.member(dimension, claim['target'], claim['source'], evidence)
        for path in cited:
            outcomes[path] = dict(status='cited', reason='An accepted claim cites a source range in this file.')
        reports[key] = dict(question=question, status=status, cited_paths=sorted(cited),
                            claims=len(claims), gap=gap)
        if absence_anchors:
            reports[key]['absence'] = shard['absence']
        coverage.append(dict(area=key, family='investigation', status='analyzed' if status == 'answered' else status,
                             reason=reason,
                             paths=sorted(cited), task=key, method=['agent-source-reading'], basis=question['question'],
                             scoped_absence=bool(absence_anchors), findings=len(claims), issues=[gap] if gap else []))

    eligible = sum(item['eligible'] for item in manifest['entries'])
    answered = sum(row['status'] == 'answered' for row in reports.values())
    scope = dict(scope='planned questions', questions=len(questions), answered=answered,
                 eligible_files=eligible, cited_files=len(outcomes), uncited_files=eligible - len(outcomes))
    for entry in manifest['entries']:
        if entry['eligible'] and entry['path'] not in outcomes:
            outcomes[entry['path']] = dict(status='unexamined', reason='No accepted source claim cites this file.')
    data = graph_store.records(manifest, plan, graph, coverage, outcomes, reports, {}, profile=profile)
    metadata = dict(data['metadata'])
    metadata.update(status=canonical('complete' if questions and answered == len(questions) else 'partial'),
                    investigation_scope=canonical(scope), accepted_shards=canonical(shards))
    data['metadata'] = list(metadata.items())
    return data
