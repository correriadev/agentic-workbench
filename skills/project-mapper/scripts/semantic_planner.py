"""Derive bounded, snapshot-specific semantic assignments from a stored graph.

Directory-based areas are scheduling buckets, not claims about architecture or
features. Unresolved and cross-unit edges are leads to investigate, not facts.
"""

from collections import defaultdict, deque
from pathlib import PurePosixPath

import graph_store
from python_profile import source_text
from scan_files import MappingError, digest


MAX_FILES_PER_UNIT = 32
MAX_NODES_PER_UNIT = 160
FRONTIER_PREVIEW = 12
FLOW_DEPTH = 5
FLOW_REFERENCES = {'imports', 'calls', 'registers', 'configures-entry', 'runs-script',
                   'declares-service', 'declares-registration', 'depends-on', 'references-project',
                   'belongs-to-project', 'uses-binding', 'uses-config'}
FLOW_ENTRIES = {'configures-entry', 'runs-script'}


def area_for(path):
    """Group by up to two directory levels without classifying their meaning."""
    parts = PurePosixPath(path).parts[:-1]
    return '/'.join(parts[:2]) or '.'


def printable(value):
    return bool(value) and value == value.strip() and value.isprintable()


def flow_questions(connection, paths_by_node):
    """Follow bounded reference leads. Keep direction and runtime review in the source investigation."""
    roots, tests = set(), set()
    for key, dimension in connection.execute(
            "SELECT node,dimension FROM memberships WHERE dimension IN "
            "('entrypoint','declared-entry-point','configuration','test','declared-test-suite')"):
        if dimension in {'test', 'declared-test-suite'}:
            tests.add(key)
        elif dimension != 'configuration' or key.startswith('mcp-server:'):
            if dimension != 'declared-entry-point' or key.startswith('entry-point:'):
                roots.add(key)
    references = defaultdict(set)
    callers, destinations = set(), set()
    for relation, source, target in connection.execute(
            "SELECT type,source,target FROM relationships WHERE family='structural' "
            "UNION ALL SELECT r.type,r.source,c.node FROM relationships r "
            "JOIN relationship_candidates c ON c.relationship=r.id WHERE r.family='structural'"):
        if relation in FLOW_ENTRIES:
            roots.add(source)
        if not target or not paths_by_node.get(source) or not paths_by_node.get(target):
            continue
        if relation in FLOW_REFERENCES:
            references[source].add(target)
            if source in tests and relation in {'imports', 'calls'}:
                references[target].add(source)
            if relation in {'imports', 'calls', 'references-project'} and source not in tests:
                if paths_by_node[source] != paths_by_node[target]:
                    callers.add(source)
                    destinations.add(target)
        elif relation in {'declares-endpoint', 'declares-tool'}:
            references[target].add(source)

    covered = set()
    remaining = callers - roots
    for anchor in [*sorted(roots), *sorted(remaining - destinations), *sorted(remaining & destinations)]:
        if (not printable(anchor) or not paths_by_node.get(anchor) or
                anchor not in roots and anchor in covered):
            continue
        keys, paths = set(), set()
        pending = deque([(anchor, 0)])
        queued = {anchor}
        truncated = False
        while pending:
            key, depth = pending.popleft()
            seeds = paths_by_node[key]
            if len(keys) == MAX_NODES_PER_UNIT:
                truncated = True
                break
            if len(paths | seeds) > MAX_FILES_PER_UNIT:
                truncated = True
                continue
            keys.add(key)
            paths.update(seeds)
            neighbors = references[key] | {'file:' + path for path in seeds if paths_by_node.get('file:' + path)}
            for neighbor in sorted(neighbors - queued):
                if not printable(neighbor):
                    continue
                if depth == FLOW_DEPTH:
                    truncated = True
                    break
                queued.add(neighbor)
                pending.append((neighbor, depth + 1))
        if not keys:
            continue
        covered.update(keys)
        yield dict(id='unit-flow-' + digest(anchor)[:24],
                   question=f'From {anchor}, which source-supported steps lead to the first material effect '
                            'or unresolved boundary, and under what conditions?',
                   seeds=sorted(paths), depends_on=[], node_ids=sorted(keys),
                   scope=dict(kind='flow', anchor=anchor)), truncated


def plan_from_graph(connection, manifest, reader=None):
    """Return an investigation plan and coverage report derived from the graph.

    All task anchors are existing graph nodes whose source paths are eligible in
    the matching inventory. Nodes observed in multiple files may be assigned to
    more than one task. Each task is bounded, but the number of tasks is not.
    """
    info = graph_store.metadata(connection, 'snapshot')
    if info.get('snapshot') != manifest.get('snapshot'):
        raise MappingError('semantic plan requires a graph for the exact input snapshot')
    entries = {entry['path']: entry for entry in manifest['entries']}
    eligible = {path for path, entry in entries.items() if entry['eligible']}
    nodes = {row['key']: dict(row) for row in connection.execute(
        'SELECT key,kind,namespace,name,external FROM nodes ORDER BY key')}

    # Occurrences preserve the real file provenance; membership by folder is
    # used only for assigning independent work, not as an architectural claim.
    raw_paths_by_node = defaultdict(set)
    for node, path in connection.execute(
            'SELECT DISTINCT n.node,o.path FROM node_observations n '
            'JOIN observations v ON v.id=n.observation '
            'JOIN occurrences o ON o.id=v.occurrence'):
        if path in eligible:
            raw_paths_by_node[node].add(path)
    for key, node in nodes.items():
        if node['kind'] == 'file' and key.startswith('file:') and key[5:] in eligible:
            raw_paths_by_node[key].add(key[5:])

    # A file node or source occurrence is not proof that the investigation
    # reader will accept the file: an extractor can anchor a file containing
    # NUL bytes. Check every eligible file against the pinned reader and the
    # same decoding and NUL rules used for investigation evidence.
    unreadable = {}
    unverified = set()
    for path in sorted(eligible):
        if not printable(path):
            continue
        if reader is None:
            unverified.add(path)
            continue
        data = reader.read(path)  # Snapshot identity errors must fail closed.
        if b'\0' in data:
            unreadable[path] = 'Contains NUL bytes; not readable as source text.'
            continue
        try:
            source_text(data, path)
        except (UnicodeError, SyntaxError, LookupError):
            unreadable[path] = 'Source encoding is not supported by the snapshot reader.'
    paths_by_node = {key: {path for path in paths if printable(path) and path not in unreadable}
                     for key, paths in raw_paths_by_node.items()}

    areas = defaultdict(lambda: defaultdict(set))
    unassigned = []
    for key, node in nodes.items():
        if node['kind'] == 'discovery':
            unassigned.append(dict(node=key, kind=node['kind'], status='semantic-result',
                                   reason='Already a semantic discovery, not an extraction anchor.'))
        elif node['external']:
            unassigned.append(dict(node=key, kind=node['kind'], status='boundary',
                                   reason='External entity; inspect its in-repository references.'))
        elif node['kind'] in {'submodule', 'symlink', 'boundary', 'pruned-directory'}:
            unassigned.append(dict(node=key, kind=node['kind'], status='boundary',
                                   reason='Inventory boundary outside eligible snapshot content.'))
        elif not printable(key):
            unassigned.append(dict(node=key, kind=node['kind'], status='pending',
                                   reason='Node identifier cannot be represented in a worker assignment.'))
        elif not paths_by_node.get(key):
            rejected_paths = raw_paths_by_node.get(key, set())
            if rejected_paths and all(path in unreadable for path in rejected_paths):
                status = 'boundary'
                reason = 'No source occurrence can be read as source text.'
            else:
                status = 'pending'
                reason = 'No eligible, representable source occurrence or file identity.'
            unassigned.append(dict(node=key, kind=node['kind'], status=status, reason=reason))
        else:
            for path in sorted(paths_by_node[key]):
                areas[area_for(path)][path].add(key)

    questions, units = [], []
    assignments = defaultdict(set)
    for area in sorted(areas):
        # Split a large file's anchors rather than exceeding the unit budget.
        fragments = []
        for path in sorted(areas[area]):
            keys = sorted(areas[area][path])
            file_key = 'file:' + path
            if len(keys) > MAX_NODES_PER_UNIT and file_key in keys:
                # Every fragment retains its file anchor, so a worker can use
                # that file's import edges even when it has many symbols.
                remaining = [key for key in keys if key != file_key]
                for start in range(0, len(remaining), MAX_NODES_PER_UNIT - 1):
                    fragments.append((path, [file_key, *remaining[start:start + MAX_NODES_PER_UNIT - 1]]))
            else:
                for start in range(0, len(keys), MAX_NODES_PER_UNIT):
                    fragments.append((path, keys[start:start + MAX_NODES_PER_UNIT]))
        pending_paths, pending_nodes = set(), set()
        batches = []
        for path, keys in fragments:
            combined_paths = pending_paths | {path}
            combined_nodes = pending_nodes | set(keys)
            if pending_nodes and (len(combined_paths) > MAX_FILES_PER_UNIT or
                                  len(combined_nodes) > MAX_NODES_PER_UNIT):
                batches.append((sorted(pending_paths), sorted(pending_nodes)))
                pending_paths, pending_nodes = set(), set()
            pending_paths.add(path)
            pending_nodes.update(keys)
        if pending_nodes:
            batches.append((sorted(pending_paths), sorted(pending_nodes)))
        for paths, keys in batches:
            task_id = 'unit-' + digest([area, paths, keys])[:24]
            task = dict(id=task_id,
                        question='What does each seed file declare or implement, and what direct boundary, if any, '
                                 'does it expose in source?',
                        seeds=paths, depends_on=[], node_ids=keys, scope=dict(kind='file'))
            questions.append(task)
            units.append(dict(id=task_id, area=area, area_basis='directory scheduling bucket',
                              initial_status='pending', path_count=len(paths), node_count=len(keys),
                              unverified_paths=[path for path in paths if path in unverified],
                              frontier_count=0, frontier_preview=[], frontier_truncated=False))
            for key in keys:
                assignments[key].add(task_id)

    for task, truncated in flow_questions(connection, paths_by_node):
        paths, keys = task['seeds'], task['node_ids']
        questions.append(task)
        units.append(dict(id=task['id'], area=area_for(min(paths_by_node[task['scope']['anchor']])),
                          area_basis='flow anchor and source references',
                          initial_status='pending', path_count=len(paths), node_count=len(keys),
                          unverified_paths=[path for path in paths if path in unverified],
                          lead_traversal_truncated=truncated,
                          frontier_count=0, frontier_preview=[], frontier_truncated=False))
        for key in keys:
            assignments[key].add(task['id'])

    unit_index = {unit['id']: unit for unit in units}
    # For each edge, count only units for which it crosses the unit boundary,
    # terminates outside the repository or has an unresolved destination.
    for edge_id, relation, family, source, target, state in connection.execute(
            'SELECT id,type,family,source,target,state FROM relationships ORDER BY id'):
        source_units = assignments.get(source, set())
        target_units = assignments.get(target, set()) if target is not None else set()
        for unit_id in source_units ^ target_units:
            unit = unit_index[unit_id]
            unit['frontier_count'] += 1
            if len(unit['frontier_preview']) < FRONTIER_PREVIEW:
                unit['frontier_preview'].append(dict(id=edge_id, type=relation, family=family,
                                                     source=source, target=target, state=state))
            else:
                unit['frontier_truncated'] = True

    plan = dict(snapshot=manifest['snapshot']['identity'], output_language='en', questions=questions)
    assigned_paths = {path for task in questions for path in task['seeds']}
    report = dict(snapshot=manifest['snapshot']['identity'],
                  strategy='Bounded file assignments and flow leads from entrypoints and source references.',
                  units=units, unassigned=unassigned,
                  unmapped_paths=sorted(eligible - assigned_paths),
                  unreadable_paths=[dict(path=path, status='boundary', reason=reason)
                                    for path, reason in sorted(unreadable.items())],
                  unverified_paths=sorted(unverified),
                  inventory_boundaries=[dict(path=path, kind=entry['kind'], status=entry['status'],
                                             reason=entry['reason']) for path, entry in sorted(entries.items())
                                        if not entry['eligible']],
                  counts=dict(nodes=len(nodes), assigned=len(assignments),
                              assigned_multiple=sum(len(value) > 1 for value in assignments.values()),
                              unassigned=len(unassigned), areas=len(areas), units=len(units)),
                  limits=dict(files_per_unit=MAX_FILES_PER_UNIT, nodes_per_unit=MAX_NODES_PER_UNIT,
                              frontier_preview=FRONTIER_PREVIEW, flow_depth=FLOW_DEPTH))
    return plan, report
