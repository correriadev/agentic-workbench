"""Build, publish, inspect and verify a source-backed repository map."""

import argparse
from collections import Counter, defaultdict
from contextlib import closing, contextmanager
from fnmatch import fnmatchcase
from graphlib import TopologicalSorter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
from uuid import uuid4

sys.dont_write_bytecode = True

import graph_store as store
from extraction_cache import ExtractionCache, extractor_identity, read_cache
from export_json import write_export
from multidimensional import PROFILE as STATIC_PROFILE, extract_graph
from csharp_profile import PROFILE as CSHARP_PROFILE
from investigation import (compile_investigation, draft_subject_diagnostics, new_plan, validate_discrepancies,
                           validate_plan, validate_shard)
from pipeline import (collect, envelope, final_coverage, load, make_plan, project, review_envelope,
                      reviews, safe_path, save, validate_baseline)
from python_profile import MANIFEST, PROFILE, Source, extract
from publication_artifacts import abandoned_stages, legacy_artifacts, publication_workspace, remove_abandoned
from resolve import reconcile
from scan_files import (MappingError, canonical, commit_changes, digest, inventory, repository, snapshot_options,
                        snapshot_reader)


OUTPUT = '.project-mapper'
RUN = re.compile(r'run-[0-9a-f]{32}\Z')
PUBLISHED_QUERIES = {'coverage', 'dimensions', 'search', 'open', 'node', 'trace'}
MULTIDIMENSIONAL_PROFILE = dict(STATIC_PROFILE, python_profile=PROFILE)
CSHARP_MULTIDIMENSIONAL_PROFILE = dict(MULTIDIMENSIONAL_PROFILE, csharp_profile=CSHARP_PROFILE)


def supported_multidimensional_profile(profile):
    return profile in (MULTIDIMENSIONAL_PROFILE, CSHARP_MULTIDIMENSIONAL_PROFILE)
# The investigation wire format derives kind from the ID prefix. Static
# profiles may use a more descriptive kind for the same exact ID.
LEGACY_KIND_ALIASES = {
    'config': {'configuration'},
    'npm-script': {'command'},
    'external-module': {'module'},
    'boundary': {'boundary', 'submodule', 'symlink', 'pruned-directory'},
    'csharp-type': {'class', 'interface', 'struct', 'record', 'enum'},
    'csharp-method': {'method'},
    'csharp-endpoint': {'endpoint'},
    'csharp-reference': {'type-reference'},
    'csharp-call': {'call-reference'},
    'csharp-registration': {'registration'},
    'dotnet-project': {'project'},
    'nuget': {'dependency'},
}


def output_paths(root, *, create=False):
    directory = safe_path(root, OUTPUT, directory=True, create=create)
    for file in ('graph.sqlite', 'README.md', 'graph.sqlite-journal', 'graph.sqlite-wal', 'graph.sqlite-shm'):
        path = safe_path(directory, file)
        if file.startswith('graph.sqlite-') and path.exists():
            raise MappingError('output graph has a SQLite sidecar; close external writers first')
    return directory, directory / 'graph.sqlite', directory / 'README.md'


def run_directory(directory, name):
    if not RUN.fullmatch(name):
        raise MappingError('invalid run ID')
    stage = safe_path(directory, name, directory=True)
    if not stage.is_dir():
        raise MappingError('run directory is unavailable')
    return stage


def graph_stamp(path):
    stat = path.stat()
    return [stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns]


def graph_fingerprint(path):
    """Hash a stable regular graph file without following a replaced symlink."""
    before = graph_stamp(path)
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    checksum = hashlib.sha256()
    with os.fdopen(os.open(path, flags), 'rb') as source:
        opened = os.fstat(source.fileno())
        handle_stamp = [opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns]
        # Windows path and handle stats can report different meanings for ctime.
        size = 4 if os.name == 'nt' else 5
        if handle_stamp[:size] != before[:size]:
            raise MappingError('graph changed while opening it')
        for block in iter(lambda: source.read(1024 * 1024), b''):
            checksum.update(block)
        after = os.fstat(source.fileno())
        if [after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns] != handle_stamp:
            raise MappingError('graph changed while hashing it')
    if graph_stamp(path) != before:
        raise MappingError('graph changed while hashing it')
    return dict(sha256=checksum.hexdigest(), stamp=before)


def save_graph_pin(stage, value):
    temporary = safe_path(stage, f'graph-pin-{uuid4().hex}.tmp')
    save(temporary, value)
    os.replace(temporary, safe_path(stage, 'graph-pin.json'))


def check_graph_pin(stage, graph_path, snapshot):
    path = safe_path(stage, 'graph-pin.json')
    if not path.is_file():
        raise MappingError('graph assignment has no verified graph fingerprint')
    pin = load(path)
    if not isinstance(pin, dict) or pin.get('snapshot') != snapshot or not isinstance(pin.get('sha256'), str):
        raise MappingError('invalid graph assignment fingerprint')
    # Windows may expose creation time as st_ctime; a same-size edit can
    # restore mtime without changing the recorded stamp. Hash on that host.
    if os.name == 'nt' or graph_stamp(graph_path) != pin.get('stamp'):
        current = graph_fingerprint(graph_path)
        alternatives = pin.get('alternates', [])
        if not isinstance(alternatives, list) or not all(isinstance(item, str) for item in alternatives):
            raise MappingError('invalid pending graph fingerprints')
        if current['sha256'] not in [pin['sha256'], *alternatives]:
            raise MappingError('assigned graph changed after verification; rebuild or revalidate the investigation')
        return current['sha256']
    return pin['sha256']


def start_run(root, commit, *, investigation=False, agent_review=False, multidimensional=False, from_graph=False,
              csharp=False):
    manifest = inventory(root, commit)
    directory, _, _ = output_paths(root, create=True)
    name = 'run-' + uuid4().hex
    stage = safe_path(directory, name, directory=True, create=True)
    shards = safe_path(stage, 'shards', directory=True, create=True)
    save(safe_path(stage, 'inventory.json'), manifest)
    result = dict(run=name, snapshot=manifest['snapshot'], plan=str(stage / 'plan.json'),
                  inventory=str(stage / 'inventory.json'), shards=str(shards))
    if investigation:
        plan = new_plan(manifest['snapshot']['identity'])
        decisions = safe_path(stage, 'decisions.json')
        save(decisions, {})
        result['decisions'] = str(decisions)
        # Pin the static profile explicitly.  Investigations started without a
        # map retain their historical publication and verification contract.
        graph_path = output_paths(root)[1]
        if from_graph and not graph_path.exists():
            raise MappingError('graph-derived investigation requires a published multidimensional graph')
        if graph_path.exists():
            opening_stamp = graph_stamp(graph_path) if from_graph else None
            with store.database(graph_path) as connection:
                if from_graph and graph_stamp(graph_path) != opening_stamp:
                    raise MappingError('graph changed while opening it; retry semantic planning')
                store.check_integrity(connection)
                current = store.metadata(connection)
                profile = current.get('multidimensional_profile', current.get('profile'))
                if from_graph:
                    if current['snapshot'] != manifest['snapshot']:
                        raise MappingError('graph snapshot differs from the requested investigation snapshot')
                    if not supported_multidimensional_profile(profile):
                        raise MappingError('graph-derived investigation requires a multidimensional graph')
                    # A graph can pass SQLite's integrity checks yet have been
                    # altered. Replay source-backed rows once before planning.
                    original_stamp = opening_stamp
                    verify(root, connection)
                    pin = graph_fingerprint(graph_path)
                    if pin['stamp'] != original_stamp:
                        raise MappingError('graph changed during verification')
                    from semantic_planner import plan_from_graph
                    with snapshot_reader(root, manifest) as reader:
                        plan, report = plan_from_graph(connection, manifest, reader)
                    if graph_stamp(graph_path) != pin['stamp']:
                        raise MappingError('graph changed during semantic planning')
                    result['graph_plan'] = str(safe_path(stage, 'graph-plan.json'))
                    save(safe_path(stage, 'graph-plan.json'), report)
                    save_graph_pin(stage, dict(snapshot=manifest['snapshot']['identity'], **pin))
                if current['snapshot'] == manifest['snapshot'] and supported_multidimensional_profile(profile):
                    save(safe_path(stage, 'static-profile.json'), profile)
    elif multidimensional:
        plan = multidimensional_plan(manifest, CSHARP_MULTIDIMENSIONAL_PROFILE if csharp else MULTIDIMENSIONAL_PROFILE)
    else:
        with snapshot_reader(root, manifest) as reader:
            plan = make_plan(manifest, reader, agent_review)
            collect(plan, reader, stage)
        result['review_tasks'] = [dict(id=key, path=str(stage / item['output']), dependencies=item['dependencies'])
                                  for key, item in plan['tasks'].items() if key.startswith('review-')]
    save(safe_path(stage, 'plan.json'), plan)
    return result


def multidimensional_rows(manifest, plan, reader, *, cache=None):
    profile = plan.get('profile')
    if plan.get('kind') != 'multidimensional' or not supported_multidimensional_profile(profile):
        raise MappingError('recorded multidimensional profile differs; use the original mapper or rebuild')
    static_profile = {key: value for key, value in profile.items() if key not in {'python_profile', 'csharp_profile'}}
    graph, coverage, outcomes, reports = extract_graph(manifest, reader, csharp='csharp_profile' in profile,
                                                       profile=static_profile, cache=cache)
    python_outcomes = {}
    for entry in manifest['entries']:
        path = entry['path']
        if entry['eligible'] and (path.endswith('.py') or path == MANIFEST):
            python_outcomes[path] = (extract(reader, path) if cache is None else
                                     cache.extract(path, entry['content_id'], 'python', lambda: extract(reader, path)))
    python_graph = reconcile(python_outcomes)
    for key, node in python_graph.nodes.items():
        if key in graph.nodes and graph.nodes[key] != node:
            raise MappingError(f'conflicting entity identity: {key}')
        graph.nodes[key] = node
    for field in ('occurrences', 'observations', 'provenance'):
        current, incoming = getattr(graph, field), getattr(python_graph, field)
        for key, value in incoming.items():
            if key in current and current[key] != value:
                raise MappingError(f'conflicting {field} identity: {key}')
            current[key] = value
    graph.node_observations.update(python_graph.node_observations)
    for key, edge in python_graph.relationships.items():
        if key in graph.relationships:
            graph.relationships[key]['evidence'].update(edge['evidence'])
        else:
            graph.relationships[key] = edge
    for key, evidence in python_graph.memberships.items():
        graph.memberships.setdefault(key, set()).update(evidence)
    graph.discrepancies.extend(python_graph.discrepancies)
    issues_by_path = defaultdict(set)
    for (issue_path, _), reasons in python_graph.issues.items():
        issues_by_path[issue_path].update(reasons)
    observations_by_path = Counter(python_graph.occurrences[item['occurrence']]['path']
                                   for item in python_graph.observations.values())
    for path, outcome in python_outcomes.items():
        issues = sorted(issues_by_path[path])
        state = outcome['status']
        reason = outcome.get('reason', '')
        if issues and state == 'analyzed':
            state = 'partial'
            reason = '; '.join(issues)
        outcomes[path] = dict(status=state, reason=reason)
        coverage.append(dict(area=path, family='python-static', status=state,
                             reason=reason or 'Python AST and supported declarations examined.',
                             task=None, paths=[path], method=['python-ast'], basis='Python profile; findings count observations',
                             scoped_absence=False, findings=observations_by_path[path], issues=issues))
    return store.records(manifest, plan, graph, coverage, outcomes, reports, {}, profile=profile)


def multidimensional_plan(manifest, profile=MULTIDIMENSIONAL_PROFILE):
    plan = dict(kind='multidimensional', snapshot=manifest['snapshot']['identity'],
                profile=profile)
    plan['id'] = digest(plan)
    return plan


def compose_multidimensional(manifest, reader, investigation, *, base=None):
    """Replay both profiles and combine evidence without rewriting their identities."""
    if base is None:
        base = multidimensional_rows(manifest, multidimensional_plan(manifest), reader)
    result = dict(investigation)
    # Inventory is shared: use extraction status, retaining cited counts in
    # investigation_scope.  Metadata retains the exact investigation plan.
    result['inventory'] = base['inventory']
    for table in ('nodes', 'occurrences', 'provenance', 'observations', 'node_observations',
                  'relationships', 'relationship_candidates', 'relationship_observations',
                  'memberships', 'membership_observations', 'tasks', 'coverage',
                  'discrepancies', 'discrepancy_observations'):
        structural = base.get(table, [])
        semantic = investigation.get(table, [])
        if table == 'nodes':
            indexed = {row[0]: row for row in structural}
            for row in semantic:
                prior = indexed.get(row[0])
                # Legacy investigation endpoints derive their displayed name
                # from the whole suffix of kind:name. Static symbols use the
                # symbol's short name. An exact identifier is the binding;
                # keep the static display and both evidence sets. Do not fold
                # discovery nodes, mismatched kinds or external endpoints.
                if prior:
                    compatible = (prior[1], prior[3], prior[4]) == (row[1], row[3], row[4])
                    prefix = row[0].partition(':')[0]
                    allowed_kinds = {prefix} | LEGACY_KIND_ALIASES.get(prefix, set())
                    legacy_identity = (row[2] == 'investigation' and ':' in row[0] and
                                       row[1] == prefix and prior[1] in allowed_kinds and
                                       row[3] == row[0].partition(':')[2] and
                                       row[4] == prior[4] == 0)
                    if not compatible and not legacy_identity:
                        raise MappingError(f'conflicting entity identity: {row[0]}')
                indexed.setdefault(row[0], row)
            result[table] = list(indexed.values())
        else:
            composite = {'coverage', 'node_observations', 'relationship_candidates',
                         'relationship_observations', 'membership_observations',
                         'discrepancy_observations'}
            indexed = {}
            for row in (*structural, *semantic):
                key = row[:2] if table in composite else row[0]
                if key in indexed and indexed[key] != row:
                    raise MappingError(f'conflicting {table} identity: {key}')
                indexed[key] = row
            result[table] = list(indexed.values())
    metadata = dict(investigation['metadata'])
    metadata['multidimensional_profile'] = dict(base['metadata'])['profile']
    if json.loads(dict(base['metadata'])['status']) != 'complete':
        metadata['status'] = canonical('partial')
    result['metadata'] = list(metadata.items())
    return result


def load_run(stage, *, allow_legacy=False):
    manifest = load(safe_path(stage, 'inventory.json'))
    plan = load(safe_path(stage, 'plan.json'))
    identity = manifest['snapshot']['identity']
    snapshot = dict(manifest['snapshot'])
    del snapshot['identity']
    if digest([snapshot, manifest['ignore_policy'], manifest['entries']]) != identity:
        raise MappingError('saved inventory fingerprint mismatch')
    if safe_path(stage, 'decisions.json').exists():
        validate_plan(plan, identity, manifest['entries'], allow_legacy=allow_legacy)
    elif plan.get('snapshot') != identity or plan.get('id') != digest({k: v for k, v in plan.items() if k != 'id'}):
        raise MappingError('saved baseline plan fingerprint mismatch')
    return manifest, plan


def question_index(plan):
    return {question['id']: question for question in plan['questions']}


def check_graph_assignment(connection, manifest, questions):
    """Ensure assigned node identities still exist in the matching graph.

    A node is a starting point, not a boundary: workers may follow other
    nodes and source files from the same snapshot.
    """
    node_ids = {node for question in questions for node in question.get('node_ids', [])}
    if not node_ids:
        return
    info = store.metadata(connection, 'snapshot')
    if info.get('snapshot') != manifest['snapshot']:
        raise MappingError('assigned graph snapshot differs from investigation snapshot')
    ordered = sorted(node_ids)
    found = set()
    for start in range(0, len(ordered), 500):
        group = ordered[start:start + 500]
        placeholders = ','.join('?' for _ in group)
        found.update(row[0] for row in connection.execute(
            f'SELECT key FROM nodes WHERE key IN ({placeholders})', group))
    missing = node_ids - found
    if missing:
        raise MappingError(f'assigned graph node is unavailable: {sorted(missing)[0]}')


def check_run_assignments(root, manifest, questions, *, stage):
    if not any(question.get('node_ids') for question in questions):
        return
    graph_path = output_paths(root)[1]
    opening_stamp = graph_stamp(graph_path)
    generation = check_graph_pin(stage, graph_path, manifest['snapshot']['identity'])
    with store.database(graph_path) as connection:
        if graph_stamp(graph_path) != opening_stamp:
            raise MappingError('graph changed while opening assignments; retry')
        store.check_schema(connection)
        check_graph_assignment(connection, manifest, questions)
    if (graph_stamp(graph_path) != opening_stamp or
            check_graph_pin(stage, graph_path, manifest['snapshot']['identity']) != generation):
        raise MappingError('graph changed while checking assignments; retry')


def published_unconditional_roles(connection, assigned):
    """Return assigned node IDs with a directly evidenced, unconditional published role.

    A full-content support pointer also supports the subject and role. This
    measures linked material, not whether the role is correct or complete.
    """
    if not assigned or connection.execute('PRAGMA user_version').fetchone()[0] == 1:
        return set()
    role_nodes = set()
    ordered = sorted(assigned)
    for start in range(0, len(ordered), 500):
        group = ordered[start:start + 500]
        values = ','.join('( ? )' for _ in group)
        query = (
            f'WITH assigned(key) AS (VALUES {values}) '
            "SELECT r.target,d.node,d.content FROM relationships r JOIN discoveries d ON d.node=r.source "
            "WHERE r.target IN (SELECT key FROM assigned) AND r.type='describes' "
            "AND r.family='semantic' AND r.state='resolved' AND r.conditions='[]' "
            "AND EXISTS (SELECT 1 FROM relationship_observations o WHERE o.relationship=r.id) "
            "AND EXISTS (SELECT 1 FROM discovery_support s WHERE s.node=d.node AND s.pointer IN ('','/subject_node')) "
            "AND EXISTS (SELECT 1 FROM discovery_support s WHERE s.node=d.node AND s.pointer IN ('','/role')) "
            'UNION ALL '
            "SELECT r.source,d.node,d.content FROM relationships r JOIN discoveries d ON d.node=r.target "
            "WHERE r.source IN (SELECT key FROM assigned) AND r.type='explained-by' "
            "AND r.family='semantic' AND r.state='resolved' AND r.conditions='[]' "
            "AND EXISTS (SELECT 1 FROM relationship_observations o WHERE o.relationship=r.id) "
            "AND EXISTS (SELECT 1 FROM discovery_support s WHERE s.node=d.node AND s.pointer IN ('','/subject_node')) "
            "AND EXISTS (SELECT 1 FROM discovery_support s WHERE s.node=d.node AND s.pointer IN ('','/role'))"
        )
        for node, _, raw in connection.execute(query, group):
            content = json.loads(raw)
            if (isinstance(content, dict) and content.get('subject_node') == node and
                    isinstance(content.get('role'), str) and content['role'].strip()):
                role_nodes.add(node)
    return role_nodes


def role_coverage(connection, node_ids):
    assigned = set(node_ids)
    covered = published_unconditional_roles(connection, assigned)
    return dict(published_unconditional_node_roles=len(covered),
                assigned_without_unconditional_role=len(assigned - covered),
                role_coverage_basis='Published, directly linked unconditional node-specific roles with supported '
                                    'subject and role; excludes unpromoted and conditional findings. '
                                    'Without-role may include conditional context and does not measure completeness.')


def check_plan(root, name, *, summary=False, question=None, listing=False, offset=0, limit=50):
    stage = run_directory(output_paths(root)[0], name)
    manifest, plan = load_run(stage)
    if 'questions' not in plan:
        raise MappingError('check-plan requires a supervisor-led investigation')
    check_run_assignments(root, manifest, plan['questions'], stage=stage)
    fingerprint = digest(plan)
    decisions = load(safe_path(stage, 'decisions.json')) if summary or question is not None or listing else {}
    if not isinstance(decisions, dict):
        raise MappingError('invalid decisions ledger')

    def progress(item):
        path = safe_path(safe_path(stage, 'shards', directory=True), item['id'] + '.json')
        if item['id'] not in decisions:
            return 'draft' if path.exists() else 'unexamined'
        try:
            raw = load(path)
            expected = decision_fingerprint(plan['output_language'], item, raw, decisions)
            if expected != decisions[item['id']] or raw.get('status') not in {'answered', 'partial', 'blocked'}:
                return 'stale'
            return 'accepted-' + raw['status']
        except (OSError, ValueError, TypeError, MappingError):
            return 'stale'

    def area(item):
        parents = [path.split('/')[:-1] for path in item['seeds']]
        prefix = []
        for parts in zip(*parents):
            if len(set(parts)) != 1:
                break
            prefix.append(parts[0])
        return '/'.join(prefix) or '.'

    if question is not None:
        item = question_index(plan).get(question)
        if item is None:
            raise MappingError('unknown investigation question')
        return dict(snapshot=plan['snapshot'], question=item, question_fingerprint=digest(item),
                    progress=progress(item), fingerprint=fingerprint)
    if listing:
        if offset < 0 or not 1 <= limit <= 500:
            raise MappingError('plan list requires a nonnegative offset and limit in 1..500')
        items = plan['questions'][offset:offset + limit]
        next_offset = offset + len(items)
        return dict(snapshot=plan['snapshot'], fingerprint=fingerprint, total=len(plan['questions']),
                    questions=[dict(id=item['id'], question=item['question'], area=area(item),
                                    **({'scope': item['scope']} if 'scope' in item else {}),
                                    progress=progress(item), seeds=len(item['seeds']),
                                    node_ids=len(item.get('node_ids', [])))
                               for item in items],
                    next_offset=next_offset if next_offset < len(plan['questions']) else None)
    if summary:
        assigned = {node for item in plan['questions'] for node in item.get('node_ids', [])}
        if assigned:
            graph_path = output_paths(root)[1]
            opening_stamp = graph_stamp(graph_path)
            generation = check_graph_pin(stage, graph_path, manifest['snapshot']['identity'])
            with store.database(graph_path) as connection:
                if graph_stamp(graph_path) != opening_stamp:
                    raise MappingError('graph changed while opening role coverage; retry')
                roles = role_coverage(connection, assigned)
            if (graph_stamp(graph_path) != opening_stamp or
                    check_graph_pin(stage, graph_path, manifest['snapshot']['identity']) != generation):
                raise MappingError('graph changed while checking role coverage; retry')
        else:
            roles = dict(published_unconditional_node_roles=0, assigned_without_unconditional_role=0,
                         role_coverage_basis='No nodes are assigned; this is not semantic completeness.')
        return dict(snapshot=plan['snapshot'], fingerprint=fingerprint, questions=len(plan['questions']),
                    graph_questions=sum(bool(item.get('node_ids')) for item in plan['questions']),
                    assigned_nodes=len(assigned), **roles,
                    progress=dict(Counter(progress(item) for item in plan['questions'])),
                    progress_basis='Stored decision fingerprint matches the current question and shard; not semantic review.')
    return dict(plan=plan, fingerprint=fingerprint)


def decision_fingerprint(output_language, question, raw, decisions):
    if not isinstance(decisions, dict):
        raise MappingError('decisions must be an object')
    dependencies = {}
    for key in question['depends_on']:
        if key not in decisions:
            raise MappingError(f'review prerequisite question first: {key}')
        dependencies[key] = decisions[key]
    return digest([{'output_language': output_language}, question, raw, dependencies])


def investigation_rows(stage, manifest, plan, reader):
    questions = question_index(plan)
    if not questions:
        raise MappingError('write the investigation questions to plan.json before publishing')
    decisions = load(safe_path(stage, 'decisions.json'))
    if not isinstance(decisions, dict) or decisions.keys() - questions.keys():
        raise MappingError('decisions must map planned question IDs to checked fingerprints')
    shard_paths = safe_path(stage, 'shards', directory=True)
    allowed = {key + '.json' for key in questions}
    if {path.name for path in shard_paths.iterdir()} - allowed:
        raise MappingError('shard directory has outputs without task ownership')
    accepted = {}
    for key, fingerprint in decisions.items():
        raw = load(safe_path(shard_paths, key + '.json'))
        if decision_fingerprint(plan['output_language'], questions[key], raw, decisions) != fingerprint:
            raise MappingError(f'review the current language contract, evidence, question and prerequisites: {key}')
        accepted[key] = raw
    return compile_investigation(manifest, plan, accepted, reader)


def import_investigation(root, source_root, source_run):
    """Copy a reviewed run to a separate C# map after replaying both snapshots."""
    source_root = repository(source_root)
    if root.resolve() == source_root.resolve():
        raise MappingError('import requires a separate target checkout; the source run remains untouched')
    source_directory, source_graph, _ = output_paths(source_root)
    stage = run_directory(source_directory, source_run)
    manifest, plan = load_run(stage)
    if 'questions' not in plan or not plan['questions']:
        raise MappingError('source must contain a nonempty investigation plan')
    opening = graph_stamp(source_graph)
    with store.database(source_graph) as connection:
        verify(source_root, connection)
        old_info = store.metadata(connection)
    if old_info.get('investigation_run') not in (None, source_run):
        raise MappingError('published source graph belongs to a different investigation run')
    check_run_assignments(source_root, manifest, plan['questions'], stage=stage)
    decisions = load(safe_path(stage, 'decisions.json'))
    if not isinstance(decisions, dict):
        raise MappingError('invalid source decisions')
    if set(old_info.get('accepted_shards', {})) - set(decisions):
        raise MappingError('published source findings are missing from current run decisions')
    shards = safe_path(stage, 'shards', directory=True)
    allowed = {item['id'] + '.json' for item in plan['questions']}
    if {p.name for p in shards.iterdir()} - allowed:
        raise MappingError('source run contains unowned shard files')
    copied = {name: load(safe_path(shards, name)) for name in sorted(allowed)
              if safe_path(shards, name).exists()}
    questions = question_index(plan)
    for key, fingerprint in decisions.items():
        if (key not in questions or key + '.json' not in copied or
                decision_fingerprint(plan['output_language'], questions[key], copied[key + '.json'], decisions) != fingerprint):
            raise MappingError('source has a stale or missing accepted shard; review it before import')
    with snapshot_reader(source_root, manifest) as reader:
        investigation_rows(stage, manifest, plan, reader)
    if manifest != inventory(root, manifest['snapshot']['revision']):
        raise MappingError('source and target inventories differ; use the exact same snapshot')
    _, target_graph, _ = output_paths(root)
    with store.database(target_graph) as connection:
        verify(root, connection)
        target_info = store.metadata(connection)
        if target_info.get('profile') != CSHARP_MULTIDIMENSIONAL_PROFILE:
            raise MappingError('target must contain a C# static map without an active investigation')
        check_graph_assignment(connection, manifest, plan['questions'])
    # Recompile all accepted evidence, and ensure it composes with the new static nodes,
    # before writing a target run. This checks structure, not the truth of agent claims.
    accepted = {key: copied[key + '.json'] for key in decisions}
    with snapshot_reader(root, manifest) as reader:
        semantic = compile_investigation(manifest, plan, accepted, reader)
        base = multidimensional_rows(manifest, multidimensional_plan(manifest, CSHARP_MULTIDIMENSIONAL_PROFILE), reader)
        compose_multidimensional(manifest, reader, semantic, base=base)
    if (graph_stamp(source_graph) != opening or load(safe_path(stage, 'plan.json')) != plan or
            load(safe_path(stage, 'decisions.json')) != decisions or
            {name: load(safe_path(shards, name)) for name in copied} != copied or
            {p.name for p in shards.iterdir()} != set(copied)):
        raise MappingError('source run changed during import; retry against a stable checkpoint')
    result = start_run(root, manifest['snapshot']['revision'], investigation=True, from_graph=True)
    destination = run_directory(output_paths(root)[0], result['run'])
    generated = load(safe_path(destination, 'plan.json'))
    assigned = {node for question in plan['questions'] for node in question.get('node_ids', [])}
    originally_assigned = assigned.copy()
    flow_anchors = {item['scope']['anchor'] for item in plan['questions']
                    if item.get('scope', {}).get('kind') == 'flow'}
    question_ids = {question['id'] for question in plan['questions']}
    added = 0
    for question in generated['questions']:
        anchor = question['scope'].get('anchor')
        if anchor in flow_anchors:
            continue
        existing = originally_assigned if anchor else assigned
        new_nodes = [node for node in question.get('node_ids', []) if node not in existing and
                     node.startswith(('csharp-', 'dotnet-project:', 'nuget:'))]
        if not new_nodes:
            continue
        question = dict(question)
        if question['id'] in question_ids:
            question['id'] = 'unit-imported-' + digest(question)[:24]
        if question['id'] in question_ids:
            raise MappingError('imported C# assignment ID collides with the source plan')
        plan['questions'].append(question)
        question_ids.add(question['id'])
        if anchor:
            flow_anchors.add(anchor)
        assigned.update(question['node_ids'])
        added += 1
    temporary_plan = safe_path(destination, f'plan-{uuid4().hex}.tmp')
    save(temporary_plan, plan)
    os.replace(temporary_plan, safe_path(destination, 'plan.json'))
    for name, raw in copied.items():
        save(safe_path(destination, 'shards/' + name), raw)
    temporary_decisions = safe_path(destination, f'decisions-{uuid4().hex}.tmp')
    save(temporary_decisions, decisions)
    os.replace(temporary_decisions, safe_path(destination, 'decisions.json'))
    # The generated report described a different plan; do not leave misleading coverage.
    report = safe_path(destination, 'graph-plan.json')
    if report.exists():
        report.unlink()
    result.pop('graph_plan', None)
    with store.database(target_graph) as connection:
        csharp_nodes = {row[0] for row in connection.execute(
            "SELECT DISTINCT n.node FROM node_observations n JOIN observations o ON o.id=n.observation "
            "WHERE o.basis IN ('csharp-tree-sitter', 'dotnet-project-xml')")}
    result.update(imported_from=source_run, accepted=len(decisions), shards=len(copied), added_questions=added,
                  unassigned_csharp_nodes=len(csharp_nodes - assigned),
                  note='Review the copied and extended plan before publishing; inspect remaining unassigned nodes.')
    return result


def expected_plan(manifest, plan, reader):
    if plan != make_plan(manifest, reader, plan['agent_review']):
        raise MappingError('saved plan does not match inventory and profile')


def replay_reviews(plan, supplemental, reader):
    keys = {key for key in plan['tasks'] if key.startswith('review-')}
    if keys != set(supplemental):
        raise MappingError('supplemental task coverage mismatch')
    for key, row in supplemental.items():
        if row == dict(task=key, status='unexamined', inputs=[], observations=[]):
            continue
        if row == dict(task=key, status='blocked', inputs=[], observations=[],
                       reason='supplemental shard failed validation'):
            continue
        data = dict(plan=plan['id'], task=key, snapshot=plan['snapshot'], status=row['status'],
                    inputs=row['inputs'], findings=[
                        dict(path=obs['path'], content_id=obs['content_id'], line=obs['span'][0],
                             kind=obs['symbol']) for obs in row['observations']])
        if review_envelope(plan, key, data, reader) != row:
            raise MappingError('supplemental observations do not reproduce from source')


def synthesize(manifest, plan, reader, baseline, supplemental):
    expected = {key for key in plan['tasks'] if key.startswith('scan-')}
    if expected != set(baseline):
        raise MappingError('baseline shard coverage mismatch')
    outcomes = {}
    for key, shard in sorted(baseline.items()):
        outcomes.update(validate_baseline(plan, key, shard, reader))
    replay_reviews(plan, supplemental, reader)
    graph = project(outcomes, supplemental)
    coverage = final_coverage(plan, manifest, outcomes, graph, supplemental)
    gaps = [dict(area=row['area'], family=row['family'], task=row['task'], reason=row['reason'],
                 next_input='review assigned paths or extend the active profile')
            for row in coverage if row['status'] not in {'analyzed', 'excluded', 'inapplicable'}]
    reports = {**baseline, **supplemental,
               'reconcile': dict(envelope(plan, 'reconcile'), relationships=len(graph.relationships),
                                 nodes=len(graph.nodes), cross_area_dependencies=plan['tasks']['reconcile']['dependencies']),
               'frontier': dict(envelope(plan, 'frontier'), gaps=gaps)}
    return store.records(manifest, plan, graph, coverage, outcomes, reports, supplemental)


def write_readme(path, info, connection, script):
    gaps = [row for row in store.coverage_records(connection)
            if row['status'] not in {'analyzed', 'excluded', 'inapplicable'}]
    counts = Counter(row['status'] for row in gaps)
    dims = [name for name, in connection.execute('SELECT DISTINCT dimension FROM memberships ORDER BY dimension')]
    item = connection.execute('SELECT source,type FROM relationships WHERE state=? ORDER BY '
                              "CASE WHEN type='calls' THEN 0 ELSE 1 END,id LIMIT 1", ('resolved',)).fetchone()
    prefix = f'python "{script.as_posix()}" .'
    commands = [f'{prefix} coverage --summary', f'{prefix} dimensions --summary', f'{prefix} verify']
    if connection.execute('SELECT 1 FROM discoveries LIMIT 1').fetchone():
        commands.extend([f'{prefix} search "<words describing the behavior>" --limit 5',
                         f'{prefix} open "<key from search>"',
                         f'{prefix} trace "<key from search>" --direction both --depth 1 --summary'])
    if item:
        commands.extend([f'{prefix} node "{item["source"]}"',
                         f'{prefix} trace "{item["source"]}" --type {item["type"]} --direction both --summary'])
    snapshot = info['snapshot']
    fence = chr(96) * 3
    content = [
        '# Project Mapper', '',
        f'- Source mode {snapshot["mode"]}',
        f'- Revision or worktree fingerprint {snapshot["revision"] or snapshot["identity"]}',
        f'- Inventory fingerprint {snapshot["identity"]}',
        f'- Profile {info["profile"]["name"]} v{info["profile"]["version"]}',
        *(['- Map language is English. Source identifiers and literals retain their original spelling.']
          if info['plan'].get('output_language') == 'en' else []),
        f'- Coverage {info["status"]}' + (' for the planned questions' if 'investigation_scope' in info else ''),
        *([f'- Cited files {info["investigation_scope"]["cited_files"]} of '
           f'{info["investigation_scope"]["eligible_files"]} eligible files'] if 'investigation_scope' in info else []),
        '- Dimensions ' + (', '.join(dims) or 'none identified'),
        '- Coverage gaps ' + (', '.join(f'{status} ({count})' for status, count in sorted(counts.items())) or 'none'),
        '', '## Material gaps', '',
        *[f'- {row["area"]} / {row["family"]} — {row["reason"]}' for row in gaps[:12]],
        '' if gaps else 'No incomplete coverage assignments.', '',
        '## Inspect from the repository root', '', fence + 'text', *commands, fence, '',
        'SQLite is authoritative for the snapshot and coverage. Use coverage --area PATH to inspect an assignment.', '',
    ]
    with path.open('x', encoding='utf-8', newline='\n') as output:
        output.write('\n'.join(content))


def baseline_rows(stage, manifest, plan, reader):
    expected_plan(manifest, plan, reader)
    shard_directory = safe_path(stage, 'shards', directory=True)
    allowed = {Path(item['output']).name for key, item in plan['tasks'].items()
               if key.startswith(('scan-', 'review-'))}
    if {item.name for item in shard_directory.iterdir()} - allowed:
        raise MappingError('shard directory has outputs without task ownership')
    baseline = {key: load(safe_path(stage, item['output'])) for key, item in plan['tasks'].items()
                if key.startswith('scan-')}
    return synthesize(manifest, plan, reader, baseline, reviews(plan, stage, reader))


@contextmanager
def write_lock(directory):
    # Serialize publication, recovery and cleanup. The OS releases the lock on exit or crash.
    for suffix in ('', '-journal', '-wal', '-shm'):
        safe_path(directory, 'publication.sqlite' + suffix)
    with closing(sqlite3.connect(directory / 'publication.sqlite', timeout=10)) as lock:
        lock.execute('BEGIN IMMEDIATE')
        yield


def scope_info(info):
    return {key: info[key] for key in ('investigation_scope', 'deferred_claims') if key in info}


def has_multidimensional_profile(info):
    profile = info.get('multidimensional_profile', info.get('profile', {}))
    return isinstance(profile, dict) and profile.get('name') == 'multidimensional-static'


def guard_promotion(path, info):
    if not path.exists():
        return
    with store.database(path) as current:
        prior = store.metadata(current)
    if prior['snapshot'] != info['snapshot']:
        return
    if has_multidimensional_profile(prior):
        if ('questions' in info['plan'] and
                info.get('multidimensional_profile') != prior.get('multidimensional_profile', prior.get('profile'))):
            raise MappingError('active multidimensional map preserved; restart investigation from the current map')
        previous_shards = prior.get('accepted_shards', {})
        proposed_shards = info.get('accepted_shards', {})
        same_run = (prior.get('investigation_run') is not None and
                    prior['investigation_run'] == info.get('investigation_run'))
        if (previous_shards.keys() - proposed_shards.keys() or
                (not same_run and any(proposed_shards.get(key) != shard
                                      for key, shard in previous_shards.items()))):
            raise MappingError('active investigation preserved; new publication omits or changes accepted findings')
    if 'questions' in prior['plan'] and 'questions' not in info['plan']:
        raise MappingError('active investigation preserved; request Python hints within the investigation')
    proposed_plan = info['plan']
    # Translation can change question IDs and wording while covering the same snapshot.
    migrating = ('questions' in prior['plan'] and 'output_language' not in prior['plan']
                 and proposed_plan.get('output_language') == 'en')
    if migrating:
        proposed_plan = {key: value for key, value in proposed_plan.items() if key != 'output_language'}
    same_plan = prior['plan'] == proposed_plan
    adding_partial_investigation = (supported_multidimensional_profile(prior.get('profile')) and
                                    info.get('multidimensional_profile') == prior.get('profile'))
    if prior['status'] == 'complete' and info['status'] != 'complete' and not adding_partial_investigation:
        raise MappingError('active complete graph preserved; new coverage is partial')
    if same_plan and set(prior.get('accepted_shards', {})) - set(info.get('accepted_shards', {})):
        raise MappingError('active investigation preserved; previously accepted questions are missing')


def stage_publication(workspace, data):
    candidate = safe_path(workspace, 'candidate.sqlite')
    candidate_readme = safe_path(workspace, 'README.md')
    store.write(candidate, data)
    with store.database(candidate) as connection:
        store.check_integrity(connection, data)
        info = store.metadata(connection)
        diagnostics = []
        if 'questions' in info['plan']:
            check_graph_assignment(connection, info, info['plan']['questions'])
            diagnostics = store.context_diagnostics(connection, limit=13)
        write_readme(candidate_readme, info, connection, Path(__file__).resolve())
    return candidate, candidate_readme, info, diagnostics


def replace_readme(candidate, path):
    try:
        os.replace(candidate, path)
    except OSError:
        return False
    return True


def publication_result(path, info, data, diagnostics, readme_written, **extra):
    result = dict(path=str(path), snapshot=info['snapshot'], status=info['status'],
                  readme_written=readme_written, relationships=len(data['relationships']), nodes=len(data['nodes']),
                  discoveries=len(data.get('discoveries', [])), supplemental_fingerprint=info['supplemental_fingerprint'],
                  **scope_info(info), **extra)
    if diagnostics:
        result.update(context_diagnostics=diagnostics[:12], context_diagnostics_truncated=len(diagnostics) > 12)
    return result


def refresh_investigation(directory, workspace, previous, manifest, profile, base, reader, *, reuse):
    """Carry reviewed answers only for a compatible transition with unchanged inputs."""
    old_plan = previous['plan']
    old_accepted = previous.get('accepted_shards', {})
    plan = new_plan(manifest['snapshot']['identity'])
    eligible = {entry['path'] for entry in manifest['entries'] if entry['eligible']}
    static_nodes = {row[0] for row in base['nodes']}
    for item in old_plan['questions']:
        question = dict(item)
        if not reuse:
            question['seeds'] = [path for path in question['seeds'] if path in eligible]
            nodes = [node for node in question.get('node_ids', []) if node in static_nodes]
            if nodes:
                question['node_ids'] = nodes
            else:
                question.pop('node_ids', None)
            scope = question.get('scope', {})
            if scope.get('kind') == 'flow' and scope['anchor'] not in nodes:
                question.pop('scope')
        plan['questions'].append(question)
    accepted = {key: dict(raw, snapshot=plan['snapshot']) for key, raw in old_accepted.items()} if reuse else {}
    semantic = compile_investigation(manifest, plan, accepted, reader)
    data = compose_multidimensional(manifest, reader, semantic, base=base)
    name = 'run-' + uuid4().hex
    stage = safe_path(workspace, name, directory=True, create=True)
    shards = safe_path(stage, 'shards', directory=True, create=True)
    questions = question_index(plan)
    decisions = {}
    for key in TopologicalSorter({key: item['depends_on'] for key, item in questions.items()}).static_order():
        if key in accepted:
            raw = accepted[key]
            decisions[key] = decision_fingerprint(plan['output_language'], questions[key], raw, decisions)
            save(safe_path(shards, key + '.json'), raw)
    for filename, value in (('inventory.json', manifest), ('plan.json', plan), ('decisions.json', decisions),
                            ('static-profile.json', profile)):
        save(safe_path(stage, filename), value)

    prior_run = previous.get('investigation_run')
    prior_review = {}
    if isinstance(prior_run, str) and RUN.fullmatch(prior_run):
        old_stage = safe_path(directory, prior_run, directory=True)
        archive = safe_path(old_stage, 'prior-review.json')
        if archive.is_file():
            prior_review = load(archive)
    if not reuse:
        previous_questions = question_index(old_plan)
        prior_review.update({key: dict(snapshot=previous['snapshot'], run=prior_run,
                                       question=previous_questions[key], shard=raw)
                             for key, raw in old_accepted.items()})
    prior_review = {key: value for key, value in prior_review.items() if key in questions and key not in accepted}
    if prior_review:
        save(safe_path(stage, 'prior-review.json'), prior_review)
    data['metadata'].append(('investigation_run', canonical(name)))
    return data, stage, plan, len(accepted), len(questions) - len(accepted)


def cached_extracts(directory, snapshot, identity):
    try:
        cache_path = safe_path(directory, 'cache.sqlite')
        if any(safe_path(directory, 'cache.sqlite' + suffix).exists()
               for suffix in ('-journal', '-wal', '-shm')):
            return cache_path, None, False
    except MappingError:
        return None, None, False
    owned, extracts = read_cache(cache_path, snapshot, identity)
    return cache_path, extracts, owned


def save_static_cache(cache_path, staged_cache, owned_cache):
    if not owned_cache:
        return 'Existing cache.sqlite was preserved because it is not a recognized mapper cache.'
    try:
        if staged_cache is None:
            cache_path.unlink(missing_ok=True)
        else:
            os.replace(staged_cache, cache_path)
    except OSError:
        return 'Graph published, but the extraction cache could not be updated.'
    return None


def map_snapshot(root, commit, csharp, *, refresh=False):
    if csharp:
        from csharp_profile import parser
        parser()  # Check the optional profile before creating any output.
    manifest = inventory(root, commit)
    snapshot = manifest['snapshot']
    directory, graph_path, readme_path = output_paths(root, create=True)
    with write_lock(directory):
        removed = remove_abandoned(directory)
        previous = {}
        generation = graph_stamp(graph_path) if graph_path.exists() else None
        if refresh and generation:
            with store.database(graph_path) as connection:
                store.check_integrity(connection)
                previous = store.metadata(connection)
        prior_snapshot = previous.get('snapshot', {})
        prior_profile = previous.get('multidimensional_profile', previous.get('profile'))
        csharp = csharp or isinstance(prior_profile, dict) and 'csharp_profile' in prior_profile
        profile = CSHARP_MULTIDIMENSIONAL_PROFILE if csharp else MULTIDIMENSIONAL_PROFILE
        base_revision = prior_snapshot.get('revision')
        if snapshot == prior_snapshot and profile == prior_profile:
            with store.database(graph_path) as connection:
                counts = {table: connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                          for table in ('nodes', 'relationships')}
                counts['discoveries'] = (connection.execute('SELECT COUNT(*) FROM discoveries').fetchone()[0]
                                         if store.check_schema(connection) >= 2 else 0)
            if graph_stamp(graph_path) != generation:
                raise MappingError('published graph changed during refresh; retry')
            return dict(path=str(graph_path), snapshot=snapshot, status=previous['status'], mode='unchanged',
                        base_revision=base_revision, changed_paths=0, extracted_files=0, reused_files=0,
                        removed=removed, run=previous.get('investigation_run'), **counts, **scope_info(previous))

        changes = None
        reason = 'no published commit' if refresh else 'full map requested'
        if (prior_snapshot.get('mode') == 'commit' and isinstance(base_revision, str)
                and re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', base_revision)):
            try:
                changes = commit_changes(root, base_revision, snapshot['revision'])
            except MappingError:
                # Missing history or unsupported diff data must not be used for reuse.
                pass
            if changes is None:
                reason = 'Git ancestry or diff unavailable'
            elif prior_profile != profile:
                reason = 'extraction profile changed'
            else:
                reason = 'compatible cache unavailable'
        identity = extractor_identity(profile)
        cache_path, old_extracts, owned_cache = cached_extracts(directory, prior_snapshot.get('identity'), identity)
        incremental = changes is not None and prior_profile == profile and old_extracts is not None
        cache = ExtractionCache(identity, old_extracts if incremental else None, changes or ())
        with publication_workspace(directory) as workspace:
            stage = None
            progress = {}
            with snapshot_reader(root, manifest) as reader:
                data = multidimensional_rows(manifest, multidimensional_plan(manifest, profile), reader, cache=cache)
                if 'questions' in previous.get('plan', {}):
                    data, stage, plan, accepted, pending = refresh_investigation(
                        directory, workspace, previous, manifest, profile, data, reader,
                        reuse=incremental and not changes)
                    progress = dict(run=stage.name, reused_questions=accepted, pending_questions=pending)
            candidate, candidate_readme, info, diagnostics = stage_publication(workspace, data)
            staged_cache = None
            if snapshot['mode'] == 'commit' and owned_cache:
                staged_cache = safe_path(workspace, 'cache.sqlite')
                cache.write(staged_cache, snapshot['identity'])
            if snapshot['mode'] == 'worktree' and manifest != inventory(root):
                raise MappingError('input snapshot changed before publication')
            output_paths(root)
            if (graph_stamp(graph_path) if graph_path.exists() else None) != generation:
                raise MappingError('published graph changed during refresh; retry')
            guard_promotion(graph_path, info)

            destination = None
            pin = None
            if stage:
                if any(question.get('node_ids') for question in plan['questions']):
                    pin = dict(snapshot=snapshot['identity'], **graph_fingerprint(candidate))
                    save_graph_pin(stage, pin)
                destination = safe_path(directory, stage.name, directory=True)
                os.rename(stage, destination)
            try:
                os.replace(candidate, graph_path)
            except OSError:
                if destination:
                    os.rename(destination, stage)
                raise
            if pin:
                promoted_stamp = graph_stamp(graph_path)
                if promoted_stamp[:4] == pin['stamp'][:4]:
                    try:
                        save_graph_pin(destination, dict(pin, stamp=promoted_stamp))
                    except OSError:
                        pass  # The original pin can still verify the exact hash.

            readme_written = replace_readme(candidate_readme, readme_path)
            cache_warning = save_static_cache(cache_path, staged_cache, owned_cache)
            return publication_result(
                graph_path, info, data, diagnostics, readme_written, mode='incremental' if incremental else 'full',
                **({'full_reason': reason} if refresh and not incremental else {}),
                base_revision=base_revision, changed_paths=len(changes) if changes is not None else None,
                extracted_files=len(cache.extracted), reused_files=len(cache.reused), removed=removed,
                **({'cache_warning': cache_warning} if cache_warning else {}), **progress)


def build_baseline(root, commit):
    manifest = inventory(root, commit)
    directory, graph_path, readme_path = output_paths(root, create=True)
    with write_lock(directory), publication_workspace(directory) as workspace:
        removed = remove_abandoned(directory, current=workspace)
        safe_path(workspace, 'shards', directory=True, create=True)
        with snapshot_reader(root, manifest) as reader:
            plan = make_plan(manifest, reader, False)
            collect(plan, reader, workspace)
            data = baseline_rows(workspace, manifest, plan, reader)
        candidate, candidate_readme, info, diagnostics = stage_publication(workspace, data)
        if commit is None and manifest != inventory(root):
            raise MappingError('input snapshot changed before publication')
        output_paths(root)
        guard_promotion(graph_path, info)
        os.replace(candidate, graph_path)
        cache_path, _, owned_cache = cached_extracts(directory, None, None)
        cache_warning = save_static_cache(cache_path, None, owned_cache)
        return publication_result(graph_path, info, data, diagnostics, replace_readme(candidate_readme, readme_path),
                                  removed=removed, **({'cache_warning': cache_warning} if cache_warning else {}))


def cleanup(root, apply=False):
    directory, graph_path, _ = output_paths(root)
    if not directory.exists():
        return dict(paths=[], removed=[])
    with write_lock(directory):
        active_run = None
        if graph_path.exists():
            with store.database(graph_path) as connection:
                active_run = store.metadata(connection, 'investigation_run').get('investigation_run')
        candidates = abandoned_stages(directory) + legacy_artifacts(directory, active_run, load_run)
        paths = [path.relative_to(directory).as_posix() for path in candidates]
        if apply:
            for path in candidates:
                shutil.rmtree(path)
        return dict(paths=paths, removed=paths if apply else [])


def publish(root, name, *, reviewed_english_plan=None):
    directory, graph_path, readme_path = output_paths(root)
    stage = run_directory(directory, name)
    manifest, plan = load_run(stage)
    replayed_base = None
    if 'questions' in plan:
        check_run_assignments(root, manifest, plan['questions'], stage=stage)
    with snapshot_reader(root, manifest) as reader:
        if 'questions' in plan:
            if reviewed_english_plan != digest(plan):
                raise MappingError('review the full current plan with check-plan and pass its fingerprint '
                                   'with --reviewed-english-plan')
            data = investigation_rows(stage, manifest, plan, reader)
            profile_path = safe_path(stage, 'static-profile.json')
            if profile_path.exists():
                static_profile = load(profile_path)
                if not supported_multidimensional_profile(static_profile):
                    raise MappingError('recorded multidimensional profile differs; use the original mapper or rebuild')
                replayed_base = multidimensional_rows(manifest, multidimensional_plan(manifest, static_profile), reader)
                data = compose_multidimensional(manifest, reader, data, base=replayed_base)
                metadata = dict(data['metadata'])
                metadata['investigation_run'] = canonical(name)
                data['metadata'] = list(metadata.items())
        elif plan.get('kind') == 'multidimensional':
            data = multidimensional_rows(manifest, plan, reader)
        else:
            data = baseline_rows(stage, manifest, plan, reader)
    # Coordinate with accept_shard (stage lock) as well as other publishers.
    with write_lock(directory), write_lock(stage), publication_workspace(directory) as workspace:
        removed = remove_abandoned(directory, current=workspace)
        candidate, candidate_readme, info, diagnostics = stage_publication(workspace, data)
        graph_assignment = 'questions' in plan and any(item.get('node_ids') for item in plan['questions'])
        candidate_pin = graph_fingerprint(candidate) if graph_assignment else None
        if manifest != inventory(root, manifest['snapshot']['revision']):
            raise MappingError('input snapshot changed before publication')
        if 'questions' in plan:
            if load(safe_path(stage, 'plan.json')) != plan:
                raise MappingError('plan changed during publication; review the current plan with check-plan')
            check_run_assignments(root, manifest, plan['questions'], stage=stage)
            if graph_assignment:
                # Replay the graph to which this run's assignments were pinned.
                with store.database(graph_path) as active:
                    verify(root, active, replayed_base=replayed_base)
            decisions = load(safe_path(stage, 'decisions.json'))
            accepted = json.loads(dict(data['metadata'])['accepted_shards'])
            if not isinstance(decisions, dict) or set(decisions) != set(accepted):
                raise MappingError('accepted findings changed during publication; retry with the current decisions')
            questions = question_index(plan)
            shards = safe_path(stage, 'shards', directory=True)
            for key, raw in accepted.items():
                current = load(safe_path(shards, key + '.json'))
                if current != raw or decision_fingerprint(plan['output_language'], questions[key], current,
                                                          decisions) != decisions[key]:
                    raise MappingError('accepted findings changed during publication; retry with the current decisions')
        output_paths(root)
        guard_promotion(graph_path, info)
        if candidate_pin:
            prior_pin = load(safe_path(stage, 'graph-pin.json'))
            save_graph_pin(stage, dict(snapshot=manifest['snapshot']['identity'], sha256=prior_pin['sha256'],
                                       alternates=[candidate_pin['sha256']], stamp=None))
        os.replace(candidate, graph_path)
        if candidate_pin:
            # The same run may continue after a progressive publication. Pin
            # the verified candidate before releasing the publication lock.
            promoted_stamp = graph_stamp(graph_path)
            if promoted_stamp[:4] != candidate_pin['stamp'][:4]:
                raise MappingError('promoted graph changed while publishing')
            save_graph_pin(stage, dict(snapshot=manifest['snapshot']['identity'],
                                       sha256=candidate_pin['sha256'], stamp=promoted_stamp))
        return publication_result(graph_path, info, data, diagnostics, replace_readme(candidate_readme, readme_path),
                                  run=stage.name, removed=removed)


def verify(root, connection, *, replayed_base=None):
    store.check_integrity(connection)
    info = store.metadata(connection)
    manifest = inventory(root, info['snapshot']['revision'])
    if manifest['snapshot'] != info['snapshot']:
        raise MappingError('current input snapshot differs from published graph')
    if replayed_base is not None:
        base_metadata = {key: json.loads(value) for key, value in replayed_base['metadata']}
        base_profile = info.get('multidimensional_profile', info.get('profile'))
        if (base_metadata.get('snapshot') != manifest['snapshot'] or
                base_metadata.get('inventory_identity') != digest(manifest) or
                base_metadata.get('profile') != base_profile or
                base_metadata.get('plan') != multidimensional_plan(manifest, base_profile)):
            raise MappingError('replayed static base differs from verification snapshot or profile')
    with snapshot_reader(root, manifest) as reader:
        if 'questions' in info['plan']:
            data = compile_investigation(manifest, info['plan'], info['accepted_shards'], reader, allow_legacy=True)
            if 'multidimensional_profile' in info:
                if not supported_multidimensional_profile(info['multidimensional_profile']):
                    raise MappingError('recorded multidimensional profile differs; use the original mapper or rebuild')
                if replayed_base is None:
                    replayed_base = multidimensional_rows(manifest, multidimensional_plan(manifest, info['multidimensional_profile']), reader)
                data = compose_multidimensional(manifest, reader, data, base=replayed_base)
                if 'investigation_run' in info:
                    if not RUN.fullmatch(info['investigation_run']):
                        raise MappingError('invalid recorded investigation run')
                    metadata = dict(data['metadata'])
                    metadata['investigation_run'] = canonical(info['investigation_run'])
                    data['metadata'] = list(metadata.items())
        elif info['plan'].get('kind') == 'multidimensional':
            if not supported_multidimensional_profile(info['profile']):
                raise MappingError('recorded multidimensional profile differs; use the original mapper or rebuild')
            data = (replayed_base if replayed_base is not None else
                    multidimensional_rows(manifest, info['plan'], reader))
        else:
            if info['profile'] != PROFILE:
                raise MappingError('recorded Python profile differs; use the original mapper to replay or rebuild')
            reports = {key: json.loads(report) for key, report in connection.execute('SELECT id,report FROM tasks')}
            baseline = {key: value for key, value in reports.items() if key.startswith('scan-')}
            expected_plan(manifest, info['plan'], reader)
            data = synthesize(manifest, info['plan'], reader, baseline, info['supplemental'])
    store.check_integrity(connection, data)
    if 'questions' in info['plan']:
        check_graph_assignment(connection, manifest, info['plan']['questions'])
    return dict(snapshot=info['snapshot'], integrity='ok', status=info['status'], **scope_info(info), entries=len(data['inventory']),
                relationships=len(data['relationships']), nodes=len(data['nodes']), discoveries=len(data.get('discoveries', [])))


def worker_prompt(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    manifest, plan = load_run(stage)
    if 'questions' not in plan:
        raise MappingError('worker-prompt requires a supervisor-led investigation')
    ids = [args.question, *args.also]
    if len(ids) != len(set(ids)):
        raise MappingError('worker batch contains duplicate questions')
    if len(ids) > 100:
        raise MappingError('a worker batch accepts at most 100 questions; dispatch additional batches')
    indexed = question_index(plan)
    if any(key not in indexed for key in ids):
        raise MappingError('unknown investigation question')
    questions = [indexed[key] for key in ids]
    check_run_assignments(root, manifest, questions, stage=stage)
    mapper = Path(__file__).resolve()
    contract = (mapper.parent.parent / 'references' / 'worker.md').read_text(encoding='utf-8').rstrip()
    common = dict(root=str(root), mapper=str(mapper), run=args.run,
                  output_language=plan['output_language'], snapshot=manifest['snapshot']['identity'],
                  plan=str(stage / 'plan.json'), inventory=str(stage / 'inventory.json'))
    if len(questions) == 1:
        question = questions[0]
        assignment = dict(**common, question=question,
                          shard=str(safe_path(stage, f'shards/{args.question}.json')))
        if question.get('node_ids'):
            assignment['graph_unit'] = dict(command='graph-unit', run=args.run, question=args.question)
    else:
        # Do not co-dispatch a prerequisite with its dependent: its accepted
        # evidence must be available before assigning the dependent question.
        if any(set(question['depends_on']).intersection(ids) for question in questions):
            raise MappingError('worker batch questions must be independent of one another')
        decisions = load(safe_path(stage, 'decisions.json'))
        if any(set(question['depends_on']) - decisions.keys() for question in questions):
            raise MappingError('accept each batch prerequisite before dispatch')
        items = []
        for question in questions:
            item = dict(id=question['id'], question=question['question'],
                        question_fingerprint=digest(question), depends_on=question['depends_on'],
                        shard=str(safe_path(stage, f"shards/{question['id']}.json")))
            if question.get('node_ids'):
                item['graph_unit'] = dict(command='graph-unit', run=args.run, question=question['id'])
            else:
                item['seeds'] = question['seeds']
            items.append(item)
        assignment = dict(**common, questions=items)
        contract = contract.replace(
            'Investigate the single question in Assignment. First compare its snapshot and question record with the matching plan entry. If either changed, return the mismatch.',
            'Investigate each independent question in Assignment.questions. For each, compare its question_fingerprint and snapshot with graph-unit or the matching plan entry. If either changed, return the mismatch for that question.')
        contract = contract.replace(
            'Return only `{"id":…,"shard":…,"lead":…,"error":…}`.',
            'Return one result per question.')
        contract += ('\n\nBatch contract: Each question owns only its indicated shard. Do not combine shards or '
                     'findings across questions. Apply the worker instructions independently to each question. '
                     'Return one result envelope per question as a JSON array, preserving failures and gaps.')
    prompt = contract + '\n\nAssignment\n' + canonical(assignment)
    if args.repair is not None:
        if not args.repair.strip():
            raise MappingError('a repair requires a concrete diagnostic')
        prompt += '\n\nRepair\n' + canonical({'diagnostic': args.repair})
    return {'prompt': prompt}


def worker_input(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    manifest, plan = load_run(stage, allow_legacy=True)
    if len(args.also) > 7:
        raise MappingError('a read accepts at most eight ranges')
    ranges = [(args.path, args.start, args.count)]
    ranges.extend((path, int(start), int(count)) for path, start, count in args.also)
    with snapshot_reader(root, manifest) as reader:
        allowed = None
        if 'questions' in plan:
            if args.task != '@' and args.task not in question_index(plan):
                raise MappingError('unknown investigation question')
        else:
            task = plan['tasks'].get(args.task)
            if not task or not args.task.startswith('review-'):
                raise MappingError('input path is outside this worker assignment')
            allowed = task['paths']
        pages = []
        source = None
        for path, start, count in ranges:
            if allowed is not None and path not in allowed:
                raise MappingError('input path is outside this worker assignment')
            if path not in reader.entries or not reader.entries[path]['eligible']:
                raise MappingError('input path is outside eligible inventory')
            if start < 1 or not 1 <= count <= 120:
                raise MappingError('start must be positive and count must be in 1..120')
            if source is None or source.path != path:
                source = Source(reader, path)
            pages.append(dict(path=path, content_id=source.content_id, start=start,
                              total_lines=len(source.lines), lines=[line.decode() for line in
                                                                   source.lines[start - 1:start - 1 + count]]))
        return {'pages': pages} if args.also else pages[0]


def draft_coverage(question, raw, pairs):
    requirements = question.get('required_relations', [])
    claims = raw['claims']
    mappings = []
    mapped = set()
    for requirement, claim in pairs:
        if not 1 <= requirement <= len(requirements) or not 1 <= claim <= len(claims):
            raise MappingError('mapping outside the 1-based requirement or claim list')
        mapped.add(requirement)
        mappings.append(dict(requirement=requirements[requirement-1], claim=claims[claim-1]))
    return dict(status=raw['status'], gap=raw['gap'], mappings=mappings,
                context_diagnostics=draft_subject_diagnostics(raw),
                unmapped=[text for i, text in enumerate(requirements, 1) if i not in mapped])


def check_shard(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    manifest, plan = load_run(stage)
    with snapshot_reader(root, manifest) as reader:
        if 'questions' in plan:
            question = question_index(plan).get(args.task)
            if question is None:
                raise MappingError('unknown investigation question')
            check_run_assignments(root, manifest, [question], stage=stage)
            raw = load(safe_path(stage, f'shards/{args.task}.json'))
            validate_shard(question['id'], raw, manifest, reader)
            validate_discrepancies(raw)
            if args.command == 'preflight':
                return draft_coverage(question, raw, args.covers)
            decisions = load(safe_path(stage, 'decisions.json'))
            fingerprint = decision_fingerprint(plan['output_language'], question, raw, decisions)
            return dict(question=args.task, status=raw['status'], claims=len(raw['claims']),
                        context_diagnostics=draft_subject_diagnostics(raw),
                        discoveries=len(raw.get('discoveries', [])), fingerprint=fingerprint)
        if args.command == 'preflight':
            raise MappingError('preflight requires an investigation question')
        task = plan['tasks'].get(args.task)
        if not task or not args.task.startswith('review-'):
            raise MappingError('task does not own a review shard')
        return review_envelope(plan, args.task, load(safe_path(stage, task['output'])), reader)


def accept_shard(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    path = safe_path(stage, 'decisions.json')
    if not path.is_file():
        raise MappingError('accept applies to supervisor-led investigations')
    with write_lock(stage):
        checked = check_shard(root, args)
        if checked['fingerprint'] != args.fingerprint:
            raise MappingError('reviewed fingerprint changed; reopen the evidence before accepting')
        decisions = load(path)
        decisions[args.task] = args.fingerprint
        temporary = safe_path(stage, f'decisions-{uuid4().hex}.tmp')
        save(temporary, decisions)
        os.replace(temporary, path)
    return checked


def search_inputs(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    manifest, _ = load_run(stage, allow_legacy=True)
    if not args.literal or not 1 <= args.limit <= 500:
        raise MappingError('supply a nonempty literal and a result limit in 1..500')
    needle = args.literal.encode()
    matches, unreadable = [], []
    with snapshot_reader(root, manifest) as reader:
        for path, entry in reader.entries.items():
            if not entry['eligible'] or (args.glob and not any(fnmatchcase(path, pat) for pat in args.glob)):
                continue
            try:
                source = Source(reader, path)
            except (UnicodeError, SyntaxError, LookupError):
                unreadable.append(path)
                continue
            if '\x00' in source.text:
                unreadable.append(path)
                continue
            for line, value in enumerate(source.lines, 1):
                if needle in value:
                    if len(matches) == args.limit:
                        return dict(matches=matches, unreadable=unreadable, truncated=True)
                    matches.append(dict(path=path, content_id=source.content_id, line=line))
    return dict(matches=matches, unreadable=unreadable, truncated=False)


def python_hints(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    manifest, _ = load_run(stage, allow_legacy=True)
    if not (args.path.endswith('.py') or args.path == MANIFEST):
        raise MappingError('Python hints support .py files and the root pyproject.toml')
    with snapshot_reader(root, manifest) as reader:
        if args.path not in reader.entries or not reader.entries[args.path]['eligible']:
            raise MappingError('input path is outside eligible inventory')
        return extract(reader, args.path)


def graph_for_run(root, run, connection):
    stage = run_directory(output_paths(root)[0], run)
    manifest, plan = load_run(stage, allow_legacy=True)
    if manifest['snapshot']['mode'] == 'worktree' and inventory(root, None) != manifest:
        raise MappingError('working-tree snapshot changed; start a new mapping run')
    info = store.metadata(connection, 'snapshot')
    if info.get('snapshot') != manifest['snapshot']:
        raise MappingError('active graph snapshot differs from investigation snapshot')
    generation = None
    if any(item.get('node_ids') for item in plan.get('questions', [])):
        generation = check_graph_pin(stage, output_paths(root)[1], manifest['snapshot']['identity'])
    return manifest, plan, generation


def graph_unit(root, args, connection):
    manifest, plan, generation = graph_for_run(root, args.run, connection)
    if 'questions' not in plan:
        raise MappingError('graph-unit requires a supervisor-led investigation')
    question = question_index(plan).get(args.question)
    if question is None or not question.get('node_ids'):
        raise MappingError('question has no graph assignment')
    if args.expect_graph is not None and args.expect_graph != generation:
        raise MappingError('graph generation changed; restart graph-unit pagination')
    if (not 1 <= args.limit <= 1000 or not 1 <= args.node_limit <= 500 or
            args.node_offset < 0 or args.edge_offset < 0):
        raise MappingError('graph-unit needs nonnegative offsets, node limit 1..500 and edge limit 1..1000')
    check_graph_assignment(connection, manifest, [question])
    result = dict(snapshot=manifest['snapshot'], graph_fingerprint=generation,
                  question=dict(id=question['id'], question=question['question'],
                    **({'scope': question['scope']} if 'scope' in question else {}),
                  depends_on=question['depends_on'], seed_count=len(question['seeds']),
                  node_count=len(question['node_ids'])), question_fingerprint=digest(question))
    result.update(role_coverage(connection, question['node_ids']))
    if not args.summary:
        selected = question['node_ids'][args.node_offset:args.node_offset + args.node_limit]
        nodes = [dict(connection.execute('SELECT key,kind,namespace,name,external FROM nodes WHERE key=?',
                                         (key,)).fetchone()) for key in selected]
        keys = question['node_ids']
        if len(keys) > connection.getlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER) - 2:
            raise MappingError('graph assignment exceeds SQLite parameter limit; split the assignment')
        values = ','.join('( ? )' for _ in keys)
        rows = connection.execute(
            f'WITH assigned(key) AS (VALUES {values}) '
            'SELECT id,type,family,source,target,state,reason,conditions FROM relationships '
            'WHERE source IN (SELECT key FROM assigned) OR target IN (SELECT key FROM assigned) '
            'ORDER BY id LIMIT ? OFFSET ?', (*keys, args.limit + 1, args.edge_offset)).fetchall()
        more_nodes = args.node_offset + len(nodes) < len(keys)
        more_edges = len(rows) > args.limit
        edges = [dict(row, conditions=json.loads(row['conditions'])) for row in rows[:args.limit]]
        for edge in edges:
            if edge['state'] == 'unresolved':
                edge['candidates'] = [row[0] for row in connection.execute(
                    'SELECT node FROM relationship_candidates WHERE relationship=? ORDER BY node', (edge['id'],))]
        result.update(seeds=question['seeds'], nodes=nodes, edges=edges,
                      next_node_offset=args.node_offset + len(nodes) if more_nodes else None,
                      next_edge_offset=args.edge_offset + args.limit if more_edges else None,
                      next_nodes=(dict(node_offset=args.node_offset + len(nodes), expect_graph=generation)
                                  if more_nodes else None),
                      next_edges=(dict(edge_offset=args.edge_offset + args.limit, expect_graph=generation)
                                  if more_edges else None),
                      truncated=more_nodes or more_edges)
    stage = run_directory(output_paths(root)[0], args.run)
    if check_graph_pin(stage, output_paths(root)[1], manifest['snapshot']['identity']) != generation:
        raise MappingError('graph generation changed during graph-unit; restart pagination')
    return result


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path, help='root of the target Git repository')
    parser.add_argument('--offline', action='store_true', help='query an existing graph without invoking Git')
    parser.add_argument('--expect-revision', metavar='COMMIT',
                        help='require this full commit hash in the published graph before querying or verifying it')
    commands = parser.add_subparsers(dest='command', required=True)
    export = commands.add_parser('export', help='export a published graph to JSON')
    export.add_argument('--output', required=True, help='new JSON filename inside .project-mapper')
    export.add_argument('--dimension', help='export one dimension and its one-hop graph neighbors')
    investigate = commands.add_parser('investigate', help='start a supervisor-authored mapping plan')
    snapshot_options(investigate)
    investigate.add_argument('--from-graph', action='store_true',
                             help='derive semantic assignments from a verified graph of the same snapshot')
    migrate = commands.add_parser('import-run', help='copy and revalidate an investigation into a separate C# checkout')
    migrate.add_argument('--source-repo', type=Path, required=True)
    migrate.add_argument('--source-run', required=True)
    map_args = commands.add_parser('map', help='publish a multidimensional static map of the snapshot')
    snapshot_options(map_args)
    map_args.add_argument('--csharp', action='store_true', help='enable the optional pinned C# syntax parser')
    refresh_args = commands.add_parser('refresh', help='update a committed map using validated Git history')
    refresh_args.add_argument('--commit', required=True, help='target Git revision to pin and map')
    refresh_args.add_argument('--csharp', action='store_true', help='enable the optional pinned C# syntax parser')
    cleanup_args = commands.add_parser('cleanup', help='list removable publication artifacts')
    cleanup_args.add_argument('--apply', action='store_true', help='remove the listed mapper-owned artifacts')
    snapshot_options(commands.add_parser('build', help='publish the optional static Python baseline'))
    prepare_args = commands.add_parser('prepare', help='inventory, plan and extract in an unpublished run')
    snapshot_options(prepare_args)
    prepare_args.add_argument('--agent-review', action='store_true')
    check_plan_args = commands.add_parser('check-plan', help='inspect the investigation plan and its fingerprint')
    check_plan_args.add_argument('run')
    plan_view = check_plan_args.add_mutually_exclusive_group()
    plan_view.add_argument('--summary', action='store_true')
    plan_view.add_argument('--question')
    plan_view.add_argument('--list', action='store_true', dest='listing')
    check_plan_args.add_argument('--offset', type=int, default=0)
    check_plan_args.add_argument('--limit', type=int, default=50)
    publish_args = commands.add_parser('publish', help='validate, resolve and atomically publish a prepared run')
    publish_args.add_argument('run')
    publish_args.add_argument('--reviewed-english-plan', metavar='FINGERPRINT',
                              help='for investigations, confirm English review of every question in this exact plan')
    worker = commands.add_parser('worker-prompt', help='render a single isolated worker assignment')
    worker.add_argument('run')
    worker.add_argument('question')
    worker.add_argument('--also', action='append', default=[], metavar='QUESTION',
                        help='dispatch independent questions together, each retaining its own shard')
    worker.add_argument('--repair', help='append one retry diagnostic to this assignment')
    read = commands.add_parser('read-input', help='read a checked, assigned worker locator')
    read.add_argument('run')
    read.add_argument('task')
    read.add_argument('path')
    read.add_argument('--start', type=int, default=1)
    read.add_argument('--count', type=int, default=40)
    read.add_argument('--also', nargs=3, metavar=('PATH', 'START', 'COUNT'), action='append', default=[],
                      help='read another known range for this assignment (up to seven additional ranges)')
    search = commands.add_parser('search-input', help='find a literal in eligible snapshot text')
    search.add_argument('run')
    search.add_argument('literal')
    search.add_argument('--glob', action='append', default=[])
    search.add_argument('--limit', type=int, default=50)
    hints = commands.add_parser('hints', help='inspect optional Python extractor candidates for one input')
    hints.add_argument('run')
    hints.add_argument('path')
    draft = commands.add_parser('preflight', help='validate an owned draft and list unmapped planned relations')
    draft.add_argument('run')
    draft.add_argument('task')
    draft.add_argument('--covers', nargs=2, type=int, action='append', default=[],
                       metavar=('REQUIREMENT', 'CLAIM'), help='inspect a proposed correspondence (1-based, repeatable)')
    check = commands.add_parser('check-shard', help='validate an assigned worker shard before publication')
    check.add_argument('run')
    check.add_argument('task')
    accept = commands.add_parser('accept', help='record the supervisor decision for an exact checked shard')
    accept.add_argument('run')
    accept.add_argument('task')
    accept.add_argument('fingerprint')
    accept.add_argument('--reviewed-english', action='store_true', required=True,
                        help='confirm the question and authored findings are in English and source literals are exact')
    coverage = commands.add_parser('coverage', help='show coverage, ignore policy and discrepancies')
    coverage.add_argument('--family')
    coverage.add_argument('--area')
    coverage.add_argument('--summary', action='store_true', help='aggregate coverage by family and status')
    dimensions = commands.add_parser('dimensions', help='show evidence-backed memberships')
    dimensions.add_argument('--summary', action='store_true', help='aggregate memberships by dimension and group')
    lookup = commands.add_parser('search', help='locate reviewed discoveries by words in their index')
    lookup.add_argument('query')
    lookup.add_argument('--limit', type=int, default=5, help='maximum candidates returned (1..100)')
    lookup.add_argument('--terms', help='search discoveries with these terms while retaining the original exact lookup')
    commands.add_parser('open', help='read one discovery and its supporting evidence by exact ID').add_argument('key')
    node = commands.add_parser('node', help='look up a node by key or exact name')
    node.add_argument('selector')
    node.add_argument('--run', help='require this investigation snapshot')
    unit = commands.add_parser('graph-unit', help='inspect one graph-derived investigation assignment')
    unit.add_argument('run')
    unit.add_argument('question')
    unit.add_argument('--summary', action='store_true', help='return compact assignment metadata')
    unit.add_argument('--node-offset', type=int, default=0)
    unit.add_argument('--node-limit', type=int, default=25)
    unit.add_argument('--edge-offset', type=int, default=0)
    unit.add_argument('--expect-graph', help='require the graph_fingerprint from the first page')
    unit.add_argument('--limit', type=int, default=100, help='maximum related edges returned (1..1000)')
    trace = commands.add_parser('trace', help='traverse typed edges and show incomplete frontiers')
    trace.add_argument('selector')
    trace.add_argument('--run', help='require this investigation snapshot')
    trace.add_argument('--direction', choices=['in', 'out', 'both'], default='out')
    trace.add_argument('--type', action='append', default=[], help='repeat for each relationship type')
    trace.add_argument('--depth', type=int, default=4)
    trace.add_argument('--max-nodes', type=int, default=100)
    trace.add_argument('--max-edges', type=int, default=250)
    trace.add_argument('--summary', action='store_true', help='summarize coverage gaps while keeping edge evidence')
    commands.add_parser('verify', help='check schema, source identity and independently replay claims')
    return parser, parser.parse_args()


def dispatch(root, args):
    if args.command == 'export':
        directory, graph_path, _ = output_paths(root)
        name = args.output
        if (not name.endswith('.json') or name in {'.json', '..json'} or '/' in name or
                '\\' in name or ':' in name or name in {'.', '..'}):
            raise MappingError('output must be a new JSON filename inside .project-mapper')
        destination = safe_path(directory, name)
        opening_stamp = graph_stamp(graph_path)
        created = False
        try:
            with store.database(graph_path) as connection:
                if graph_stamp(graph_path) != opening_stamp:
                    raise MappingError('graph changed while opening export; retry')
                store.check_integrity(connection)
                snapshot = store.metadata(connection, 'snapshot')['snapshot']
                with destination.open('x', encoding='utf-8', newline='\n') as output:
                    created = True
                    counts = write_export(connection, output, dimension=args.dimension)
                    if graph_stamp(graph_path) != opening_stamp:
                        raise MappingError('graph changed during export; retry')
            return dict(path=str(destination), snapshot=snapshot,
                        dimension=args.dimension, counts=counts)
        except BaseException:
            if created:
                destination.unlink(missing_ok=True)
            raise
    if args.command == 'investigate':
        return start_run(root, args.commit, investigation=True, from_graph=args.from_graph)
    if args.command == 'import-run':
        return import_investigation(root, args.source_repo, args.source_run)
    if args.command in {'map', 'refresh'}:
        return map_snapshot(root, args.commit, args.csharp, refresh=args.command == 'refresh')
    if args.command == 'cleanup':
        return cleanup(root, args.apply)
    if args.command == 'build':
        return build_baseline(root, args.commit)
    if args.command == 'prepare':
        return start_run(root, args.commit, agent_review=args.agent_review)
    if args.command == 'check-plan':
        return check_plan(root, args.run, summary=args.summary, question=args.question,
                          listing=args.listing, offset=args.offset, limit=args.limit)
    if args.command == 'publish':
        return publish(root, args.run, reviewed_english_plan=args.reviewed_english_plan)
    if args.command == 'worker-prompt':
        return worker_prompt(root, args)
    if args.command == 'read-input':
        return worker_input(root, args)
    if args.command == 'search-input':
        return search_inputs(root, args)
    if args.command == 'hints':
        return python_hints(root, args)
    if args.command == 'accept':
        return accept_shard(root, args)
    if args.command in ('preflight', 'check-shard'):
        return check_shard(root, args)
    graph_path = output_paths(root)[1]
    pinned_query = args.command == 'graph-unit' or (args.command in {'node', 'trace'} and args.run)
    opening_stamp = graph_stamp(graph_path) if pinned_query else None
    with store.database(graph_path) as connection:
        if pinned_query and graph_stamp(graph_path) != opening_stamp:
            raise MappingError('graph changed while opening query; retry')
        store.check_schema(connection)
        if args.expect_revision:
            snapshot = store.metadata(connection, 'snapshot')['snapshot']
            if snapshot['mode'] != 'commit':
                raise MappingError('expected a committed graph, found a worktree snapshot')
            if snapshot['revision'] != args.expect_revision.lower():
                raise MappingError(f"published graph revision {snapshot['revision']} differs from "
                                   f"expected revision {args.expect_revision.lower()}")
        if args.command == 'graph-unit':
            result = graph_unit(root, args, connection)
            if graph_stamp(graph_path) != opening_stamp:
                raise MappingError('graph changed during graph-unit query; retry')
            return result
        if args.command == 'coverage':
            if args.summary:
                return store.summarize_coverage(connection, args.family, args.area)
            return store.inspect_coverage(connection, args.family, args.area)
        if args.command == 'dimensions':
            if args.summary:
                return dict(dimensions=store.summarize_dimensions(connection))
            return dict(memberships=store.dimensions(connection))
        if args.command == 'search':
            matches = store.search_discoveries(connection, args.query, args.limit, terms=args.terms)
            info = store.metadata(connection, 'snapshot', 'profile', 'multidimensional_profile')
            result = dict(snapshot=info['snapshot'], matches=matches)
            if supported_multidimensional_profile(info.get('profile')) or 'multidimensional_profile' in info:
                result['nodes'] = store.search_nodes(connection, args.query, args.limit)
            return result
        if args.command == 'open':
            discovery = store.open_discovery(connection, args.key)
            return dict(snapshot=store.metadata(connection, 'snapshot')['snapshot'], **discovery)
        if args.command == 'node':
            if args.run:
                manifest, plan, generation = graph_for_run(root, args.run, connection)
                result = dict(snapshot=manifest['snapshot'], nodes=store.inspect_node(connection, args.selector))
                stage = run_directory(output_paths(root)[0], args.run)
                if any(item.get('node_ids') for item in plan.get('questions', [])):
                    if check_graph_pin(stage, output_paths(root)[1], manifest['snapshot']['identity']) != generation:
                        raise MappingError('graph generation changed during node query; retry')
                if graph_stamp(graph_path) != opening_stamp:
                    raise MappingError('graph changed during node query; retry')
                return result
            return dict(nodes=store.inspect_node(connection, args.selector))
        if args.command == 'trace':
            if not 0 <= args.depth <= 100 or not 1 <= args.max_nodes <= 10000 or not 1 <= args.max_edges <= 20000:
                raise MappingError('trace bounds outside depth 0..100, nodes 1..10000 or edges 1..20000')
            if args.run:
                manifest, plan, generation = graph_for_run(root, args.run, connection)
            result = store.trace(connection, args.selector, args.direction, args.type, args.depth,
                                 args.max_nodes, args.max_edges, summary=args.summary)
            if args.run:
                stage = run_directory(output_paths(root)[0], args.run)
                if any(item.get('node_ids') for item in plan.get('questions', [])):
                    if check_graph_pin(stage, output_paths(root)[1], manifest['snapshot']['identity']) != generation:
                        raise MappingError('graph generation changed during trace query; retry')
                if graph_stamp(graph_path) != opening_stamp:
                    raise MappingError('graph changed during trace query; retry')
            return result
        return verify(root, connection)


def main():
    parser, args = arguments()
    try:
        if args.expect_revision is not None:
            if args.command not in PUBLISHED_QUERIES | {'verify'}:
                raise MappingError('--expect-revision is supported for published graph queries and verify')
            if not re.fullmatch(r'[0-9a-fA-F]{40}|[0-9a-fA-F]{64}', args.expect_revision):
                raise MappingError('--expect-revision requires a full Git commit hash')
        if args.offline:
            if args.command not in PUBLISHED_QUERIES or getattr(args, 'run', None):
                raise MappingError('offline mode supports published graph queries without run assignments only')
            root = args.repo.resolve(strict=True)
            if not root.is_dir():
                raise MappingError('target root must be a directory')
            graph = output_paths(root)[1]
            before = graph_fingerprint(graph)
            with store.database(graph) as connection:
                store.check_integrity(connection)
                info = store.metadata(connection, 'snapshot', 'status', 'profile')
            result = dispatch(root, args)
            after = graph_fingerprint(graph)
            if before != after:
                raise MappingError('graph changed during offline query; retry')
            result['graph_identity'] = dict(sha256=before['sha256'], **info,
                                            current_snapshot_verified=False)
        else:
            result = dispatch(repository(args.repo), args)
        print(canonical(result))
    except (MappingError, OSError, sqlite3.Error, ValueError, KeyError, TypeError, LookupError, SyntaxError) as error:
        parser.exit(1, f'project-mapper: {error}\n')


if __name__ == '__main__':
    main()
