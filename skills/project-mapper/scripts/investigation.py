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
    return {'snapshot': identity, 'output_language': 'en', 'questions': []}


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


def validate_plan(plan, identity, entries, *, allow_legacy=False):
    if allow_legacy and isinstance(plan, dict) and 'output_language' not in plan:
        fields(plan, 'snapshot questions', 'investigation plan')
    else:
        fields(plan, 'snapshot output_language questions', 'investigation plan')
        if plan['output_language'] != 'en':
            raise MappingError('investigation plan requires output_language "en"')
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


def node_id(value, entries):
    string(value, 'node id')
    if value.startswith('file:'):
        path = value.removeprefix('file:')
        if path not in entries or not entries[path]['eligible']:
            raise MappingError(f'file endpoint outside the eligible snapshot: {path}')


def legacy_node(key):
    kind, sep, name = key.partition(':')
    if not sep or not SLUG.fullmatch(kind) or not name or name != name.strip():
        raise MappingError(f'endpoint has no accepted discovery or valid legacy kind:name key: {key}')
    return kind, name


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


def check_pointer(pointer, content):
    if not isinstance(pointer, str) or (pointer and not pointer.startswith('/')):
        raise MappingError('expected a JSON pointer relative to discovery content')
    try:
        pointer.encode('utf-8')
    except UnicodeEncodeError as error:
        raise MappingError('JSON pointer must contain valid Unicode') from error
    current = content
    for part in pointer.split('/')[1:]:
        if re.search(r'~(?![01])', part):
            raise MappingError(f'invalid JSON pointer escape: {pointer!r}')
        token = part.replace('~1', '/').replace('~0', '~')
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif (isinstance(current, list) and re.fullmatch(r'0|[1-9][0-9]*', token)
              and len(token) <= len(str(len(current))) and int(token) < len(current)):
            current = current[int(token)]
        else:
            raise MappingError(f'JSON pointer does not resolve in discovery content: {pointer!r}')


def checked_discoveries(discoveries, question_id, reader, read_source):
    checked = {}
    for item in discoveries:
        fields(item, 'id title summary terms content support', 'discovery')
        key = item['id']
        string(key, 'discovery id')
        if len(key) > 256 or ':' in key:
            raise MappingError("discovery id must be at most 256 characters and cannot contain ':' (reserved for endpoints)")
        if key in checked:
            raise MappingError(f'duplicate discovery id: {key}')
        string(item['title'], 'discovery title')
        string(item['summary'], 'discovery summary')
        for term in string_list(item['terms'], 'discovery terms'):
            string(term, 'discovery term')
        try:
            content = canonical(item['content'])
        except (TypeError, ValueError, RecursionError) as error:
            raise MappingError('discovery content must be finite JSON') from error
        if not isinstance(item['support'], list) or not item['support']:
            raise MappingError('discovery support must cite at least one content fragment')
        support = []
        for fragment in item['support']:
            fields(fragment, 'pointer evidence', 'discovery support')
            pointer = fragment['pointer']
            check_pointer(pointer, item['content'])
            support.append((pointer, evidence_ranges(fragment['evidence'], question_id, reader, read_source)))
        checked[key] = (item, content, support)
    return checked


def checked_findings(question_id, raw, manifest, reader, read_source):
    required = 'snapshot question status claims gap'
    if isinstance(raw, dict):
        required += ''.join(' ' + key for key in ('absence', 'discoveries') if key in raw)
    fields(raw, required, 'investigation shard')
    if raw['snapshot'] != manifest['snapshot']['identity'] or raw['question'] != question_id:
        raise MappingError('shard question or snapshot mismatch')
    status, claims, gap = raw['status'], raw['claims'], raw['gap']
    discoveries = raw.get('discoveries', [])
    has_absence = 'absence' in raw
    if (status not in ('answered', 'partial', 'blocked') or not isinstance(claims, list)
            or not isinstance(discoveries, list)):
        raise MappingError('invalid shard status, claims or discoveries')
    string(gap, 'evidence gap', empty=True)
    positive = bool(claims or discoveries)
    if has_absence and (status != 'answered' or positive):
        raise MappingError('a scoped absence requires an answered question with zero positive findings')
    if status == 'answered' and (not positive and not has_absence or gap):
        raise MappingError('an answered question requires an evidenced finding or scoped absence and no gap')
    if status != 'answered' and not gap:
        raise MappingError('a partial or blocked question requires a concrete gap')
    if status == 'blocked' and positive:
        raise MappingError('use partial for a question with both supported findings and a gap')

    checked = []
    for claim in claims:
        fields(claim, 'source relation target condition evidence', 'claim')
        node_id(claim['source'], reader.entries)
        node_id(claim['target'], reader.entries)
        slug(claim['relation'], 'relation')
        string(claim['condition'], 'condition', empty=True)
        checked.append((claim, evidence_ranges(claim['evidence'], question_id, reader, read_source)))
    absence_anchors = []
    if has_absence:
        absence = raw['absence']
        fields(absence, 'statement evidence', 'scoped absence')
        string(absence['statement'], 'scoped absence statement')
        absence_anchors = evidence_ranges(absence['evidence'], question_id, reader, read_source)
    return checked, absence_anchors, checked_discoveries(discoveries, question_id, reader, read_source)


def validate_shard(question_id, raw, manifest, reader):
    """Check the envelope, endpoints and cited bytes. The supervisor assesses meaning."""
    read_source = lru_cache(maxsize=8)(partial(evidence_text, reader))
    checked_findings(question_id, raw, manifest, reader, read_source)
    return raw


def compile_investigation(manifest, plan, shards, reader, *, allow_legacy=False):
    """Rebuild logical rows from the accepted subset, retaining every planned question."""
    validate_plan(plan, manifest['snapshot']['identity'], manifest['entries'], allow_legacy=allow_legacy)
    questions = {item['id']: item for item in plan['questions']}
    if not isinstance(shards, dict) or shards.keys() - questions.keys():
        raise MappingError('accepted shards must belong to the investigation plan')
    read_source = lru_cache(maxsize=8)(partial(evidence_text, reader))
    checked = {key: checked_findings(key, raw, manifest, reader, read_source) for key, raw in shards.items()}
    titles = {}
    for _, _, discoveries in checked.values():
        for key, (item, _, _) in discoveries.items():
            if key in titles:
                raise MappingError(f'duplicate discovery id: {key}')
            titles[key] = item['title']
    relations = sorted({claim['relation'] for claims, _, _ in checked.values() for claim, _ in claims})
    profile = dict(name='agent-investigation', version=2 if titles else 1,
                   edge_types={'semantic': relations, 'structural': []})
    graph = Graph(profile=profile)
    coverage, reports, outcomes = [], {}, {}
    discovery_rows, support_rows = [], set()
    for key, question in questions.items():
        shard = shards.get(key)
        status = shard['status'] if shard else 'unexamined'
        gap = shard['gap'] if shard else 'No supervisor-accepted answer for this question.'
        claims, absence_anchors, discoveries = checked.get(key, ([], [], {}))
        cited = {anchor['path'] for anchor in absence_anchors}
        reason = gap or 'Planned question answered with supervisor-reviewed source claims.'
        if absence_anchors:
            reason = shard['absence']['statement']
            sources = [graph.observe(anchor, 'agent-scoped-absence', 'source', 'Absence scoped to the question.')
                       for anchor in absence_anchors]
            graph.discrepancy('scoped-absence', absence_anchors[0]['path'], reason, sources)
        for node, (item, content, support) in discoveries.items():
            discovery_rows.append((node, item['title'], item['summary'], canonical(item['terms']), content))
            for pointer, anchors in support:
                cited.update(anchor['path'] for anchor in anchors)
                evidence = [graph.observe(anchor, 'agent-discovery-reading', 'source',
                                          'Supervisor-reviewed source support for the indicated content fragment.')
                            for anchor in anchors]
                graph.node(node, 'discovery', 'investigation', item['title'], evidence)
                support_rows.update((node, pointer, ev) for ev in evidence)
        for claim, anchors in claims:
            limitation = 'Supervisor-reviewed static claim; verification replays source locators.'
            if claim['condition']:
                limitation += ' Condition: ' + claim['condition']
            evidence = [graph.observe(anchor, 'agent-source-reading', 'source', limitation) for anchor in anchors]
            cited.update(anchor['path'] for anchor in anchors)
            for node in (claim['source'], claim['target']):
                kind, name = ('discovery', titles[node]) if node in titles else legacy_node(node)
                graph.node(node, kind, 'investigation', name, evidence)
            graph.relation(claim['relation'], claim['source'], claim['target'], 'resolved', evidence,
                           conditions=[claim['condition']] if claim['condition'] else [])
            if claim['relation'] == 'member-of':
                dimension = graph.nodes[claim['target']]['kind']
                graph.member(dimension, claim['target'], claim['source'], evidence)
        for path in cited:
            outcomes[path] = dict(status='cited', reason='An accepted claim cites a source range in this file.')
        reports[key] = dict(question=question, status=status, cited_paths=sorted(cited),
                            claims=len(claims), gap=gap)
        if discoveries:
            reports[key]['discoveries'] = len(discoveries)
        if absence_anchors:
            reports[key]['absence'] = shard['absence']
        methods = (['agent-source-reading'] if claims or not discoveries else [])
        if discoveries:
            methods.append('agent-discovery-reading')
        coverage.append(dict(area=key, family='investigation', status='analyzed' if status == 'answered' else status,
                             reason=reason, paths=sorted(cited), task=key, method=methods, basis=question['question'],
                             scoped_absence=bool(absence_anchors), findings=len(claims) + len(discoveries),
                             issues=[gap] if gap else []))

    eligible = sum(item['eligible'] for item in manifest['entries'])
    answered = sum(row['status'] == 'answered' for row in reports.values())
    scope = dict(scope='planned questions', questions=len(questions), answered=answered,
                 eligible_files=eligible, cited_files=len(outcomes), uncited_files=eligible - len(outcomes))
    for entry in manifest['entries']:
        if entry['eligible'] and entry['path'] not in outcomes:
            outcomes[entry['path']] = dict(status='unexamined', reason='No accepted source claim cites this file.')
    data = graph_store.records(manifest, plan, graph, coverage, outcomes, reports, {}, profile=profile)
    if discovery_rows:
        data['discoveries'] = discovery_rows
        data['discovery_support'] = sorted(support_rows)
    metadata = dict(data['metadata'])
    metadata.update(status=canonical('complete' if questions and answered == len(questions) else 'partial'),
                    investigation_scope=canonical(scope), accepted_shards=canonical(shards))
    data['metadata'] = list(metadata.items())
    return data
