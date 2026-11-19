"""Canonical SQLite schema, integrity checks, and read-only projections."""

from collections import deque
from contextlib import closing, contextmanager
import json
import sqlite3

from python_profile import PROFILE
from scan_files import MappingError, canonical, digest


SCHEMA_VERSION = 1
SCHEMA = """
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL) STRICT;
CREATE TABLE inventory (path TEXT PRIMARY KEY, kind TEXT NOT NULL, content_id TEXT, eligible INTEGER NOT NULL,
                        tracked INTEGER NOT NULL, status TEXT NOT NULL, reason TEXT NOT NULL, raw_path TEXT) STRICT;
CREATE TABLE nodes (key TEXT PRIMARY KEY, kind TEXT NOT NULL, namespace TEXT NOT NULL,
                    name TEXT NOT NULL, external INTEGER NOT NULL CHECK(external IN (0,1))) STRICT;
CREATE TABLE occurrences (id TEXT PRIMARY KEY, path TEXT NOT NULL REFERENCES inventory(path), content_id TEXT NOT NULL,
                          span TEXT NOT NULL, kind TEXT NOT NULL, symbol TEXT NOT NULL, excerpt_digest TEXT NOT NULL,
                          UNIQUE(path, content_id, span, kind, symbol, excerpt_digest)) STRICT;
CREATE TABLE provenance (id TEXT PRIMARY KEY, profile TEXT NOT NULL, version INTEGER NOT NULL, method TEXT NOT NULL) STRICT;
CREATE TABLE observations (id TEXT PRIMARY KEY, occurrence TEXT NOT NULL REFERENCES occurrences(id),
                           context TEXT NOT NULL REFERENCES provenance(id), basis TEXT NOT NULL,
                           authority TEXT NOT NULL CHECK(authority IN ('source','declaration','candidate')),
                           limitation TEXT NOT NULL) STRICT;
CREATE TABLE node_observations (node TEXT NOT NULL REFERENCES nodes(key), observation TEXT NOT NULL REFERENCES observations(id),
                                PRIMARY KEY(node,observation)) STRICT;
CREATE TABLE relationships (id TEXT PRIMARY KEY, type TEXT NOT NULL,
                            family TEXT NOT NULL CHECK(family IN ('structural','semantic')),
                            source TEXT NOT NULL REFERENCES nodes(key), target TEXT REFERENCES nodes(key),
                            state TEXT NOT NULL CHECK(state IN ('resolved','unresolved','declared-external')),
                            conditions TEXT NOT NULL, reason TEXT NOT NULL, discriminator TEXT NOT NULL,
                            CHECK((target IS NULL) = (state = 'unresolved'))) STRICT;
CREATE TABLE relationship_candidates (relationship TEXT NOT NULL REFERENCES relationships(id),
                                      node TEXT NOT NULL REFERENCES nodes(key), PRIMARY KEY(relationship,node)) STRICT;
CREATE TABLE relationship_observations (relationship TEXT NOT NULL REFERENCES relationships(id),
                                        observation TEXT NOT NULL REFERENCES observations(id),
                                        PRIMARY KEY(relationship,observation)) STRICT;
CREATE TABLE memberships (id TEXT PRIMARY KEY, dimension TEXT NOT NULL, group_key TEXT NOT NULL,
                          node TEXT NOT NULL REFERENCES nodes(key), UNIQUE(dimension,group_key,node)) STRICT;
CREATE TABLE membership_observations (membership TEXT NOT NULL REFERENCES memberships(id),
                                      observation TEXT NOT NULL REFERENCES observations(id),
                                      PRIMARY KEY(membership,observation)) STRICT;
CREATE TABLE tasks (id TEXT PRIMARY KEY, status TEXT NOT NULL, report TEXT NOT NULL) STRICT;
CREATE TABLE coverage (area TEXT NOT NULL, family TEXT NOT NULL, status TEXT NOT NULL, reason TEXT NOT NULL,
                       task TEXT REFERENCES tasks(id), paths TEXT NOT NULL, method TEXT NOT NULL,
                       basis TEXT NOT NULL, scoped_absence INTEGER NOT NULL CHECK(scoped_absence IN (0,1)),
                       findings INTEGER NOT NULL, issues TEXT NOT NULL, PRIMARY KEY(area,family)) STRICT;
CREATE TABLE discrepancies (id TEXT PRIMARY KEY, kind TEXT NOT NULL, path TEXT NOT NULL REFERENCES inventory(path),
                            reason TEXT NOT NULL) STRICT;
CREATE TABLE discrepancy_observations (discrepancy TEXT NOT NULL REFERENCES discrepancies(id),
                                       observation TEXT NOT NULL REFERENCES observations(id),
                                       PRIMARY KEY(discrepancy,observation)) STRICT;
CREATE INDEX nodes_name ON nodes(name);
CREATE INDEX occurrences_path ON occurrences(path);
CREATE INDEX relationships_source ON relationships(source,type,id);
CREATE INDEX relationships_target ON relationships(target,type,id);
CREATE INDEX relationship_candidates_node ON relationship_candidates(node,relationship);
"""


def records(manifest, plan, graph, coverage, outcomes, reports, supplemental):
    complete = all(row['status'] in {'analyzed', 'excluded', 'inapplicable'} for row in coverage)
    inventory_rows = []
    for item in manifest['entries']:
        outcome = outcomes.get(item['path'], {})
        status, reason = item['status'], item['reason']
        if status == 'pending':
            status = outcome.get('status', 'unexamined')
            reason = outcome.get('reason', 'no active profile signal' if not outcome else '')
        if status in {'blocked', 'unsupported'}:
            complete = False
        inventory_rows.append((item['path'], item['kind'], item['content_id'], int(item['eligible']),
                               int(item['tracked']), status, reason, item.get('raw_path')))
    metadata = dict(schema_version=SCHEMA_VERSION, profile=PROFILE, snapshot=manifest['snapshot'],
                    inventory_identity=digest(manifest), ignore_policy=manifest['ignore_policy'],
                    plan=plan, status='complete' if complete else 'partial',
                    supplemental=supplemental, supplemental_fingerprint=digest(supplemental) if any(
                        row['observations'] or row['inputs'] for row in supplemental.values()) else None)
    members = [(digest(key), *key) for key in graph.memberships]
    discrepancy_rows = {digest(item): item for item in graph.discrepancies}
    return {
        'metadata': [(key, canonical(value)) for key, value in metadata.items()],
        'inventory': inventory_rows,
        'nodes': [(key, item['kind'], item['namespace'], item['name'], int(item['external']))
                  for key, item in graph.nodes.items()],
        'occurrences': [(key, a['path'], a['content_id'], canonical(a['span']), a['kind'], a['symbol'],
                         a['excerpt_digest']) for key, a in graph.occurrences.items()],
        'provenance': [(key, item['profile'], item['version'], item['method']) for key, item in graph.provenance.items()],
        'observations': [(key, item['occurrence'], item['context'], item['basis'], item['authority'],
                          item['limitation']) for key, item in graph.observations.items()],
        'node_observations': list(graph.node_observations),
        'relationships': [(key, item['type'], item['family'], item['source'], item['target'], item['state'],
                           canonical(item['conditions']), item['reason'], item['discriminator'])
                          for key, item in graph.relationships.items()],
        'relationship_candidates': [(key, target) for key, item in graph.relationships.items()
                                    for target in item['candidates']],
        'relationship_observations': [(key, ev) for key, item in graph.relationships.items() for ev in item['evidence']],
        'memberships': members,
        'membership_observations': [(item_id, ev) for item_id, *key in members for ev in graph.memberships[tuple(key)]],
        'tasks': [(key, entry['status'], canonical(entry)) for key, entry in reports.items()],
        'coverage': [(row['area'], row['family'], row['status'], row['reason'], row['task'], canonical(row['paths']),
                      canonical(row['method']), row['basis'], int(row['scoped_absence']), row['findings'],
                      canonical(row['issues'])) for row in coverage],
        'discrepancies': [(key, item['kind'], item['path'], item['reason']) for key, item in discrepancy_rows.items()],
        'discrepancy_observations': [(key, ev) for key, item in discrepancy_rows.items() for ev in item['evidence']],
    }


@contextmanager
def database(path):
    if not path.is_file():
        raise MappingError(f'graph database unavailable: {path}')
    connection = sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        connection.execute('PRAGMA trusted_schema=OFF')
        connection.row_factory = sqlite3.Row
        yield connection
    finally:
        connection.close()


def write(path, data):
    with path.open('xb'):
        pass
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA trusted_schema=OFF')
        connection.executescript(SCHEMA)
        connection.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
        for table, rows in data.items():
            if rows:
                parameters = ','.join('?' for _ in rows[0])
                connection.executemany(f'INSERT INTO {table} VALUES ({parameters})', sorted(rows, key=canonical))


def schema_rows(connection):
    return [tuple(row) for row in connection.execute(
        'SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE sql IS NOT NULL ORDER BY name')]


def check_schema(connection):
    with closing(sqlite3.connect(':memory:')) as reference:
        reference.executescript(SCHEMA)
        expected = schema_rows(reference)
    if (connection.execute('PRAGMA user_version').fetchone()[0] != SCHEMA_VERSION
            or schema_rows(connection) != expected):
        raise MappingError('graph schema does not match this version')


def check_integrity(connection, expected=None):
    check_schema(connection)
    if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise MappingError('SQLite integrity check failed')
    if connection.execute('PRAGMA foreign_key_check').fetchone():
        raise MappingError('graph foreign key check failed')
    invalid = (
        'SELECT 1 FROM occurrences o JOIN inventory i USING(path) WHERE o.content_id IS NOT i.content_id',
        "SELECT 1 FROM relationships r JOIN nodes n ON r.target=n.key "
        "WHERE (r.state='declared-external') != n.external",
        "SELECT 1 FROM relationship_candidates c JOIN relationships r ON c.relationship=r.id "
        "WHERE r.state!='unresolved'",
        'SELECT 1 FROM relationships WHERE id NOT IN (SELECT relationship FROM relationship_observations)',
        'SELECT 1 FROM memberships WHERE id NOT IN (SELECT membership FROM membership_observations)',
        "SELECT 1 FROM coverage WHERE scoped_absence AND (status!='analyzed' OR findings!=0)",
    )
    if any(connection.execute(query + ' LIMIT 1').fetchone() for query in invalid):
        raise MappingError('graph evidence or coverage integrity check failed')
    if expected:
        for table, rows in expected.items():
            actual = [tuple(row) for row in connection.execute(f'SELECT * FROM {table}')]
            if sorted(actual, key=canonical) != sorted(rows, key=canonical):
                raise MappingError(f'graph rows do not reproduce from validated evidence: {table}')


def metadata(connection):
    return {key: json.loads(value) for key, value in connection.execute('SELECT key,value FROM metadata')}


def evidence(connection, table, column, key):
    # Table and column are internal constants supplied by the projections below.
    query = f"""
       SELECT v.id,o.path,o.content_id,o.span,o.kind,o.symbol,o.excerpt_digest,
              v.basis,v.authority,v.limitation,p.id AS context,p.profile,p.version,p.method
       FROM {table} x JOIN observations v ON x.observation=v.id
       JOIN occurrences o ON v.occurrence=o.id JOIN provenance p ON v.context=p.id
       WHERE x.{column}=? ORDER BY o.path,o.span,v.id
    """
    return [dict(row, span=json.loads(row['span'])) for row in connection.execute(query, (key,))]


def edge_record(connection, row):
    key = row['id']
    return dict(row, conditions=json.loads(row['conditions']), evidence=evidence(
        connection, 'relationship_observations', 'relationship', key), candidates=[
            node for node, in connection.execute('SELECT node FROM relationship_candidates WHERE relationship=? '
                                                 'ORDER BY node', (key,))])


def coverage_records(connection, *, family=None, area=None):
    query = 'SELECT * FROM coverage WHERE (? IS NULL OR family=?) AND (? IS NULL OR area=?) ORDER BY area,family'
    return [dict(row, paths=json.loads(row['paths']), method=json.loads(row['method']),
                 issues=json.loads(row['issues']), scoped_absence=bool(row['scoped_absence']))
            for row in connection.execute(query, (family, family, area, area))]


def inspect_coverage(connection, family=None, area=None):
    info = metadata(connection)
    discrepancies = [dict(row, evidence=evidence(connection, 'discrepancy_observations', 'discrepancy', row['id']))
                     for row in connection.execute('SELECT * FROM discrepancies ORDER BY path,kind,id')]
    return dict(snapshot=info['snapshot'], status=info['status'], profile=info['profile'],
                ignore_policy=info['ignore_policy'], coverage=coverage_records(connection, family=family, area=area),
                discrepancies=discrepancies)


def dimensions(connection):
    return [dict(row, evidence=evidence(connection, 'membership_observations', 'membership', row['id']))
            for row in connection.execute('SELECT * FROM memberships ORDER BY dimension,group_key,node')]


def find_nodes(connection, selector):
    query = 'SELECT * FROM nodes WHERE key=? OR name=? ORDER BY key'
    result = connection.execute(query, (selector, selector)).fetchall()
    if not result:
        raise MappingError('no matching node key or exact name')
    return result


def adjacent(connection, key, direction, types, upward=False):
    outgoing = 'source=?' if direction in {'out', 'both'} and not upward else '0'
    incoming = 'target=?' if direction in {'in', 'both'} else '0'
    params = (key,) * (outgoing.count('?') + incoming.count('?'))
    query = f'SELECT * FROM relationships WHERE ({outgoing} OR {incoming})'
    if upward:
        query += " AND type='contains'"
    if types:
        query += ' AND type IN (' + ','.join('?' for _ in types) + ')'
    return connection.execute(query + ' ORDER BY id', (*params, *types))


def incoming_candidates(connection, key, types=()):
    query = ('SELECT r.* FROM relationships r JOIN relationship_candidates c ON c.relationship=r.id '
             'WHERE c.node=?')
    if types:
        query += ' AND type IN (' + ','.join('?' for _ in types) + ')'
    return connection.execute(query + ' ORDER BY r.id', (key, *types))


def inspect_node(connection, selector):
    return [dict(row,
                 evidence=evidence(connection, 'node_observations', 'node', row['key']),
                 incoming=[edge_record(connection, item) for item in adjacent(connection, row['key'], 'in', [])],
                 outgoing=[edge_record(connection, item) for item in adjacent(connection, row['key'], 'out', [])],
                 incoming_candidates=[edge_record(connection, item) for item in incoming_candidates(connection, row['key'])])
            for row in find_nodes(connection, selector)]


def trace(connection, selector, direction, types, depth, max_nodes, max_edges):
    seeds = [row['key'] for row in find_nodes(connection, selector)]
    nodes = set(seeds[:max_nodes])
    queue = deque((key, 0, False) for key in seeds[:max_nodes])
    visited, edges, unresolved = set(), {}, {}
    limits = {'nodes'} if len(seeds) > max_nodes else set()

    def record_unknown(row):
        if row['id'] in unresolved:
            return
        if len(unresolved) >= max_edges:
            limits.add('unresolved-edges')
        else:
            unresolved[row['id']] = row

    while queue:
        key, level, upward = queue.popleft()
        if (key, upward) in visited:
            continue
        visited.add((key, upward))
        if direction in {'in', 'both'} and not upward:
            for row in incoming_candidates(connection, key, types):
                record_unknown(row)
        for row in adjacent(connection, key, direction, types, upward):
            if row['state'] == 'unresolved':
                record_unknown(row)
                continue
            other = row['source'] if row['target'] == key else row['target']
            if row['id'] in edges and other in nodes:
                continue
            if level >= depth:
                limits.add('depth')
                continue
            if other not in nodes and len(nodes) >= max_nodes:
                limits.add('nodes')
                continue
            if len(edges) >= max_edges:
                limits.add('edges')
                continue
            nodes.add(other)
            edges[row['id']] = row
            queue.append((other, level + 1, row['type'] == 'contains' and row['target'] == key))
    relevant = {family for family, kinds in PROFILE['edge_types'].items() if not types or set(types).intersection(kinds)}
    gaps = [dict(area=row['area'], family=row['family'], status=row['status'], reason=row['reason'])
            for row in coverage_records(connection) if row['family'] in relevant
            and row['status'] not in {'analyzed', 'inapplicable', 'excluded'}]
    return dict(snapshot=metadata(connection)['snapshot'], seeds=seeds[:max_nodes], nodes=sorted(nodes),
                edges=[edge_record(connection, row) for _, row in sorted(edges.items())],
                truncated=bool(limits), limits=sorted(limits), analysis_incomplete=bool(gaps or unresolved),
                coverage_frontier=gaps,
                unresolved_frontier=[edge_record(connection, row) for _, row in sorted(unresolved.items())])
