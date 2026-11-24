"""Canonical SQLite schema, integrity checks, and read-only projections."""

from collections import deque
from contextlib import closing, contextmanager
import json
from pathlib import PurePosixPath
import re
import sqlite3
import unicodedata

from python_profile import PROFILE
from scan_files import MappingError, canonical, digest


SCHEMA_VERSION = 2
SCHEMA_V1 = """
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
SCHEMA = SCHEMA_V1 + """
CREATE TABLE discoveries (node TEXT PRIMARY KEY REFERENCES nodes(key), title TEXT NOT NULL, summary TEXT NOT NULL,
                          terms TEXT NOT NULL, content TEXT NOT NULL) STRICT;
CREATE TABLE discovery_support (node TEXT NOT NULL REFERENCES discoveries(node), pointer TEXT NOT NULL,
                                observation TEXT NOT NULL REFERENCES observations(id),
                                PRIMARY KEY(node,pointer,observation)) STRICT, WITHOUT ROWID;
CREATE TABLE discovery_terms (term TEXT NOT NULL, node TEXT NOT NULL REFERENCES discoveries(node),
                              weight INTEGER NOT NULL, PRIMARY KEY(term,node)) STRICT, WITHOUT ROWID;
CREATE INDEX coverage_open ON coverage(family,area) WHERE status NOT IN ('analyzed','inapplicable','excluded');
"""


def tokens(text):
    folded = unicodedata.normalize('NFKD', text.casefold())
    folded = ''.join(char for char in folded if not unicodedata.combining(char))
    return set(re.findall(r'[^\W_]+', folded))


def search_rows(discoveries):
    for key, title, summary, terms, _ in discoveries:
        weights = dict.fromkeys(tokens(summary), 1)
        weights.update(dict.fromkeys(tokens(' '.join(json.loads(terms))), 2))
        weights.update(dict.fromkeys(tokens(title) | tokens(key), 3))
        for term, weight in sorted(weights.items()):
            yield term, key, weight


def records(manifest, plan, graph, coverage, outcomes, reports, supplemental, *, profile=PROFILE):
    complete = all(row['status'] in {'analyzed', 'excluded', 'inapplicable'} for row in coverage)
    inventory_rows = []
    for item in manifest['entries']:
        outcome = outcomes.get(item['path'], {})
        status, reason = item['status'], item['reason']
        if status == 'pending':
            status = outcome.get('status', 'unexamined')
            reason = outcome.get('reason', 'no active profile signal' if not outcome else '')
        if status in {'blocked', 'unsupported', 'unexamined', 'partial'}:
            complete = False
        inventory_rows.append((item['path'], item['kind'], item['content_id'], int(item['eligible']),
                               int(item['tracked']), status, reason, item.get('raw_path')))
    metadata = dict(schema_version=SCHEMA_VERSION, profile=profile, snapshot=manifest['snapshot'],
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
        connection.executemany('INSERT INTO discovery_terms VALUES (?,?,?)', search_rows(data.get('discoveries', [])))


def schema_rows(connection):
    return [tuple(row) for row in connection.execute(
        'SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE sql IS NOT NULL ORDER BY name')]


def check_schema(connection):
    version = connection.execute('PRAGMA user_version').fetchone()[0]
    if version not in (1, SCHEMA_VERSION):
        raise MappingError('graph schema does not match this version')
    with closing(sqlite3.connect(':memory:')) as reference:
        reference.executescript(SCHEMA_V1 if version == 1 else SCHEMA)
        expected = schema_rows(reference)
    if schema_rows(connection) != expected:
        raise MappingError('graph schema does not match this version')
    return version


def check_integrity(connection, expected=None):
    version = check_schema(connection)
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
    if version >= 2:
        invalid += ('SELECT 1 FROM discoveries d WHERE NOT EXISTS '
                    '(SELECT 1 FROM discovery_support s WHERE s.node=d.node)',)
    if any(connection.execute(query + ' LIMIT 1').fetchone() for query in invalid):
        raise MappingError('graph evidence or coverage integrity check failed')
    if expected:
        tables = {'discoveries': [], 'discovery_support': []} | expected
        if version == 1:
            if tables.pop('discoveries') or tables.pop('discovery_support'):
                raise MappingError('version 1 graphs cannot reproduce discoveries')
            tables['metadata'] = [(key, '1' if key == 'schema_version' else value)
                                  for key, value in tables['metadata']]
        else:
            tables['discovery_terms'] = list(search_rows(tables['discoveries']))
        for table, rows in tables.items():
            actual = [tuple(row) for row in connection.execute(f'SELECT * FROM {table}')]
            if sorted(actual, key=canonical) != sorted(rows, key=canonical):
                raise MappingError(f'graph rows do not reproduce from validated evidence: {table}')


def metadata(connection, *keys):
    query = 'SELECT key,value FROM metadata'
    if keys:
        query += ' WHERE key IN (' + ','.join('?' for _ in keys) + ')'
    return {key: json.loads(value) for key, value in connection.execute(query, keys)}


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
    info = metadata(connection, 'snapshot', 'status', 'profile', 'ignore_policy', 'investigation_scope', 'deferred_claims')
    discrepancies = [dict(row, evidence=evidence(connection, 'discrepancy_observations', 'discrepancy', row['id']))
                     for row in connection.execute('SELECT * FROM discrepancies ORDER BY path,kind,id')]
    return dict(snapshot=info['snapshot'], status=info['status'], profile=info['profile'],
                ignore_policy=info['ignore_policy'], coverage=coverage_records(connection, family=family, area=area),
                inventory_counts=dict(connection.execute('SELECT status,count(*) FROM inventory GROUP BY status')),
                **({'investigation_scope': info['investigation_scope']} if 'investigation_scope' in info else {}),
                **investigation_metrics(connection, info, family, area),
                context_diagnostics=context_diagnostics(connection, question=area),
                deferred_claims=[claim for claim in info.get('deferred_claims', [])
                                 if area is None or claim['question'] == area],
                reviewed_discrepancies=reviewed_discrepancies(connection, question=area),
                discrepancies=discrepancies)


def semantic_context_counts(connection):
    """Count direct discovery links; this is not a measure of understanding."""
    if connection.execute('PRAGMA user_version').fetchone()[0] == 1:
        rows = connection.execute(
            "SELECT kind,count(*) AS total,0 AS linked,count(*) AS not_linked FROM nodes "
            "WHERE kind!='discovery' GROUP BY kind ORDER BY kind")
    else:
        rows = connection.execute(
            "WITH linked(node) AS ("
            "SELECT r.source FROM relationships r JOIN discoveries d ON d.node=r.target "
            "WHERE r.family='semantic' AND r.state='resolved' AND r.type='explained-by' UNION "
            "SELECT r.target FROM relationships r JOIN discoveries d ON d.node=r.source "
            "WHERE r.family='semantic' AND r.state='resolved' AND r.type='describes') "
            "SELECT n.kind,count(*) AS total,"
            "sum(CASE WHEN linked.node IS NULL THEN 0 ELSE 1 END) AS linked,"
            "sum(CASE WHEN linked.node IS NULL THEN 1 ELSE 0 END) AS not_linked "
            "FROM nodes n LEFT JOIN linked ON linked.node=n.key "
            "WHERE n.kind!='discovery' GROUP BY n.kind ORDER BY n.kind")
    return dict(scope='repository-wide', nodes_by_kind=[dict(row) for row in rows],
                basis='Distinct non-discovery nodes directly described by a discovery or linked by explained-by; '
                      'not-linked does not imply absence of context or measure semantic completeness.')


def summarize_coverage(connection, family=None, area=None):
    info = metadata(connection, 'snapshot', 'status', 'profile', 'ignore_policy', 'investigation_scope')
    rows = connection.execute(
        'SELECT family,status,count(*) AS count FROM coverage '
        'WHERE (? IS NULL OR family=?) AND (? IS NULL OR area=?) '
        'GROUP BY family,status ORDER BY family,status', (family, family, area, area))
    return dict(snapshot=info['snapshot'], status=info['status'], profile=info['profile'],
                ignore_policy=info['ignore_policy'], summary=[dict(row) for row in rows],
                inventory_counts=dict(connection.execute('SELECT status,count(*) FROM inventory GROUP BY status')),
                discrepancy_count=connection.execute('SELECT count(*) FROM discrepancies').fetchone()[0],
                semantic_context=semantic_context_counts(connection),
                **investigation_metrics(connection, info, family, area),
                **({'investigation_scope': info['investigation_scope']} if 'investigation_scope' in info else {}))


def investigation_metrics(connection, info, family, area):
    scope = info.get('investigation_scope', {})
    counts = dict(connection.execute(
        "SELECT t.status,count(*) FROM tasks t JOIN coverage c ON c.task=t.id "
        "WHERE c.family='investigation' AND json_extract(t.report,'$.question.scope.kind')='flow' "
        "AND (? IS NULL OR c.family=?) AND (? IS NULL OR c.area=?) GROUP BY t.status ORDER BY t.status",
        (family, family, area, area)))
    return dict(file_citation=dict(eligible_files=scope.get('eligible_files', connection.execute(
                    'SELECT count(*) FROM inventory WHERE eligible=1').fetchone()[0]),
                    cited_files=scope.get('cited_files', 0), basis='Files cited by published investigation findings.'),
                flow_investigation=dict(statuses=counts, basis='Recorded outcomes of explicitly scoped flow questions.'))


def context_diagnostics(connection, *, node=None, question=None, limit=-1):
    if connection.execute('PRAGMA user_version').fetchone()[0] == 1:
        return []
    rows = connection.execute("""
        WITH subjects AS (
            SELECT node,json_extract(content,'$.subject_node') AS subject,
                   json_type(content,'$.subject_node') AS value_type
            FROM discoveries WHERE json_type(content,'$.subject_node') IS NOT NULL
        )
        SELECT d.*, EXISTS (SELECT 1 FROM discovery_support s
                            WHERE s.node=d.node AND s.pointer IN ('','/subject_node')) AS supported,
               NOT EXISTS (SELECT 1 FROM relationships r JOIN relationship_observations o ON o.relationship=r.id
                           WHERE r.source=d.node AND r.target=d.subject AND r.type='describes'
                           AND r.family='semantic' AND r.state='resolved')
               AND NOT EXISTS (SELECT 1 FROM relationships r JOIN relationship_observations o ON o.relationship=r.id
                               WHERE r.source=d.subject AND r.target=d.node AND r.type='explained-by'
                               AND r.family='semantic' AND r.state='resolved') AS missing
        FROM subjects d WHERE (? IS NULL OR d.node=? OR (d.value_type='text' AND d.subject=?))
          AND (? IS NULL OR EXISTS (SELECT 1 FROM discovery_support s
              JOIN observations v ON v.id=s.observation JOIN occurrences o ON o.id=v.occurrence
              WHERE s.node=d.node AND o.symbol=?))
          AND (d.value_type!='text' OR d.subject='' OR NOT supported OR missing)
        ORDER BY d.node LIMIT ?
    """, (node, node, node, question, question, limit))
    diagnostics = []
    for row in rows:
        key, target = row['node'], row['subject']
        valid = row['value_type'] == 'text' and target and target.isprintable() and target == target.strip()
        if not valid:
            status, reason = 'invalid-subject', 'Use an exact node ID, or omit subject_node for shared context.'
        elif row['missing']:
            status, reason = 'missing-subject-link', 'Add a cited describes or explained-by claim in an accepted shard.'
            if not row['supported']:
                reason += ' Cite source support for /subject_node as well.'
        else:
            status, reason = 'unsupported-subject', 'Cite source support for /subject_node.'
        locators = connection.execute(
            "SELECT DISTINCT o.path,o.content_id,o.span FROM discovery_support s "
            "JOIN observations v ON v.id=s.observation JOIN occurrences o ON o.id=v.occurrence "
            "WHERE s.node=? AND s.pointer IN ('','/subject_node') ORDER BY o.path,o.span LIMIT ?",
            (key, SEMANTIC_EVIDENCE_LIMIT))
        diagnostics.append(dict(discovery=key, subject_node=target if row['value_type'] == 'text' else None,
                                status=status, reason=reason, open=key,
                                evidence=[dict(ref, span=json.loads(ref['span'])) for ref in locators]))
    return diagnostics


def reviewed_discrepancies(connection, *, nodes=(), question=None):
    if connection.execute('PRAGMA user_version').fetchone()[0] == 1:
        return []
    query = ("SELECT r.* FROM relationships r JOIN discoveries left_side ON left_side.node=r.source "
             "JOIN discoveries right_side ON right_side.node=r.target WHERE r.type='conflicts-with' "
             "AND r.family='semantic' AND r.state='resolved' AND r.source!=r.target")
    params = ()
    if nodes:
        marks = ','.join('?' for _ in nodes)
        query += f' AND (r.source IN ({marks}) OR r.target IN ({marks}))'
        params = (*nodes, *nodes)
    if question is not None:
        query += (' AND EXISTS (SELECT 1 FROM relationship_observations x JOIN observations v ON v.id=x.observation '
                  'JOIN occurrences o ON o.id=v.occurrence WHERE x.relationship=r.id AND o.symbol=?)')
        params += (question,)
    return [edge_record(connection, row) for row in connection.execute(query + ' ORDER BY r.id', params)]


def dimensions(connection):
    return [dict(row, evidence=evidence(connection, 'membership_observations', 'membership', row['id']))
            for row in connection.execute('SELECT * FROM memberships ORDER BY dimension,group_key,node')]


def summarize_dimensions(connection):
    return [dict(row) for row in connection.execute(
        'SELECT dimension,group_key,count(*) AS count FROM memberships '
        'GROUP BY dimension,group_key ORDER BY dimension,group_key')]


def find_nodes(connection, selector):
    exact = connection.execute('SELECT * FROM nodes WHERE key=?', (selector,)).fetchone()
    if exact:
        return [exact]
    result = connection.execute('SELECT * FROM nodes WHERE name=? ORDER BY key', (selector,)).fetchall()
    if not result:
        raise MappingError('no matching node key or exact name')
    return result


def adjacent(connection, key, direction, types, upward=False):
    endpoints = []
    if direction in {'out', 'both'} and not upward:
        endpoints.append('source=?')
    if direction in {'in', 'both'}:
        endpoints.append('target=?')
    if not endpoints:
        return ()
    params = (key,) * len(endpoints)
    query = 'SELECT * FROM relationships WHERE (' + ' OR '.join(endpoints) + ')'
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


def search_anchors(connection, query):
    """Find exact structural identifiers and file basenames or stems."""
    rows = connection.execute(
        "SELECT key,kind,name FROM nodes WHERE kind!='discovery' AND "
        "(key=? OR name=? OR (kind='file' AND instr('/'||name,'/'||?)>0)) "
        "ORDER BY key", (query, query, query))
    for row in rows:
        if query in (row['key'], row['name']):
            yield row['key']
        elif row['kind'] == 'file':
            path = PurePosixPath(row['name'])
            if query in (path.name, path.stem):
                yield row['key']


def search_discoveries(connection, query, limit, *, terms=None):
    if not 1 <= limit <= 100:
        raise MappingError('search limit must be between 1 and 100')
    query = query.strip()
    if not query:
        raise MappingError('search requires a query')
    if terms is not None and not terms.strip():
        raise MappingError('search terms must not be empty')
    if connection.execute('PRAGMA user_version').fetchone()[0] == 1:
        return []
    # Preview fields precede content in the row. Do not decode the authored JSON to route a reader.
    preview = ("SELECT d.node AS key,CASE WHEN length(d.title)>160 THEN substr(d.title,1,159)||'…' "
               "ELSE d.title END AS title,CASE WHEN length(d.summary)>320 THEN substr(d.summary,1,319)||'…' "
               "ELSE d.summary END AS summary FROM discoveries d")
    exact = connection.execute(preview + ' WHERE d.node=?', (query,)).fetchone()
    hits = [dict(exact)] if exact else []
    if len(hits) == limit:
        return hits
    words = sorted(tokens(query if terms is None else terms))
    if len(words) > 128:
        raise MappingError('search accepts up to 128 distinct words per query')
    marks = ','.join('?' for _ in words)
    anchors = list(search_anchors(connection, query))
    if anchors:
        # Use keywords to disambiguate source identities with the same short name.
        linked = ("WITH anchors AS (SELECT value AS key FROM json_each(?)), linked AS ("
                  "SELECT r.source AS node FROM anchors a JOIN relationships r ON r.target=a.key "
                  "WHERE r.type='describes' AND r.family='semantic' AND r.state='resolved' UNION "
                  "SELECT r.target FROM anchors a JOIN relationships r ON r.source=a.key "
                  "WHERE r.type='explained-by' AND r.family='semantic' AND r.state='resolved'), "
                  "scores AS (SELECT t.node,COUNT(*) AS matches,SUM(t.weight) AS score "
                  "FROM discovery_terms t JOIN linked l ON l.node=t.node "
                  f"WHERE t.term IN ({marks}) GROUP BY t.node) ")
        sql = (linked + preview + ' JOIN linked l ON l.node=d.node LEFT JOIN scores s ON s.node=d.node '
               'WHERE d.node!=? ORDER BY s.matches DESC,s.score DESC,(lower(d.title)=lower(?)) DESC,d.node LIMIT ?')
        params = (canonical(anchors), *words, query, query, limit - len(hits))
        hits.extend(dict(row) for row in connection.execute(sql, params))
    if not words or len(hits) == limit:
        return hits
    # Limit candidates before fetching previews. Exact keys take precedence over lexical matches.
    ranked = ('WITH ranked AS (SELECT node,COUNT(*) AS matches,SUM(weight) AS score FROM discovery_terms '
              f'WHERE term IN ({marks}) AND node NOT IN (SELECT value FROM json_each(?)) '
              'GROUP BY node ORDER BY matches DESC,score DESC,node LIMIT ?) ')
    sql = ranked + preview + ' JOIN ranked r ON d.node=r.node ORDER BY r.matches DESC,r.score DESC,r.node'
    selected = canonical([query, *(item['key'] for item in hits)])
    hits.extend(dict(row) for row in connection.execute(sql, (*words, selected, limit - len(hits))))
    return hits


def search_nodes(connection, query, limit):
    """Find bounded structural candidates without claiming semantic relevance."""
    if not 1 <= limit <= 100:
        raise MappingError('search limit must be between 1 and 100')
    query = query.strip()
    if not query:
        raise MappingError('search requires a query')
    rows = connection.execute(
        'SELECT key,kind,namespace,name,external FROM nodes '
        'WHERE instr(lower(name),lower(?)) > 0 OR instr(lower(key),lower(?)) > 0 '
        'ORDER BY CASE WHEN key=? THEN 0 WHEN name=? THEN 1 ELSE 2 END, length(name),key LIMIT ?',
        (query, query, query, query, limit))
    return [dict(row) for row in rows]


def discovery_record(connection, key, *, support_limit=None):
    row = connection.execute('SELECT node AS key,title,summary,terms,content FROM discoveries WHERE node=?',
                             (key,)).fetchone()
    if row is None:
        return None
    support = {}
    # A snapshot, blob and span suffice to reopen a source. The node projection also exposes full provenance.
    locators = """
        SELECT s.pointer,v.id,o.path,o.content_id,o.span FROM discovery_support s
        JOIN observations v ON v.id=s.observation JOIN occurrences o ON o.id=v.occurrence
        WHERE s.node=? ORDER BY s.pointer,o.path,o.span,v.id
    """
    if support_limit is None:
        rows = connection.execute(locators, (key,)).fetchall()
    else:
        rows = connection.execute(locators + ' LIMIT ?', (key, support_limit + 1)).fetchall()
    for pointer, observation, path, content_id, span in rows[:support_limit]:
        support.setdefault(pointer, []).append(dict(id=observation, path=path, content_id=content_id,
                                                     span=json.loads(span)))
    result = dict(row, terms=json.loads(row['terms']), content=json.loads(row['content']),
                  support=[dict(pointer=ptr, evidence=items) for ptr, items in support.items()])
    if support_limit is not None:
        result['support_truncated'] = len(rows) > support_limit
    return result


def open_discovery(connection, key):
    if connection.execute('PRAGMA user_version').fetchone()[0] != 1:
        result = discovery_record(connection, key)
        if result is not None:
            return result
    raise MappingError('no discovery with this exact key in the published map')


def related_discoveries(connection, key, limit=8, *, contextual_only=False, flows_only=False):
    """Return bounded previews of reviewed discoveries directly linked to a node.

    A missing link means only that no direct discovery is present in this
    snapshot; it is not a statement that the node has no semantic context.
    """
    if connection.execute('PRAGMA user_version').fetchone()[0] == 1:
        return [], False
    outgoing_filter = " AND r.type='explained-by'" if contextual_only else ''
    incoming_filter = " AND r.type='describes'" if contextual_only else ''
    if flows_only:
        flow = (" AND EXISTS (SELECT 1 FROM discovery_support s WHERE s.node=d.node "
                "AND ((s.pointer='' AND json_type(d.content,'$.flow') NOT IN ('null')) "
                "OR s.pointer='/flow' OR s.pointer LIKE '/flow/%'))")
        outgoing_filter = " AND r.type IN ('explained-by','participates-in')" + flow
        incoming_filter = " AND r.type IN ('describes','includes-step')" + flow
    preview = (
        "SELECT r.id,r.type AS relation,'outgoing' AS direction,d.node AS key,r.conditions,"
        "CASE WHEN length(d.title)>160 THEN substr(d.title,1,159)||'…' ELSE d.title END AS title,"
        "CASE WHEN length(d.summary)>320 THEN substr(d.summary,1,319)||'…' ELSE d.summary END AS summary "
        "FROM relationships r JOIN discoveries d ON d.node=r.target "
        "WHERE r.source=? AND r.family='semantic' AND r.state='resolved' " + outgoing_filter +
        "UNION ALL "
        "SELECT r.id,r.type AS relation,'incoming' AS direction,d.node AS key,r.conditions,"
        "CASE WHEN length(d.title)>160 THEN substr(d.title,1,159)||'…' ELSE d.title END AS title,"
        "CASE WHEN length(d.summary)>320 THEN substr(d.summary,1,319)||'…' ELSE d.summary END AS summary "
        "FROM relationships r JOIN discoveries d ON d.node=r.source "
        "WHERE r.target=? AND r.family='semantic' AND r.state='resolved' " + incoming_filter +
        'ORDER BY key,relation,direction,id LIMIT ?'
    )
    rows = connection.execute(preview, (key, key, limit + 1)).fetchall()
    items = []
    for row in rows[:limit]:
        item = dict(row)
        item['relation_id'] = item.pop('id')
        item['conditions'] = json.loads(item['conditions'])
        item['evidence'] = evidence(connection, 'relationship_observations', 'relationship', item['relation_id'])
        items.append(item)
    return items, len(rows) > limit


SEMANTIC_FIELDS = ('role', 'purpose', 'behavior', 'flow', 'participates_in', 'entrypoints',
                   'dependencies', 'configuration', 'inputs', 'outputs', 'conditions',
                   'related_tests', 'gaps', 'limits')
SEMANTIC_VALUE_LIMIT = 2048
SEMANTIC_EVIDENCE_LIMIT = 8
SEMANTIC_FRAGMENTS_LIMIT = 8
SEMANTIC_SUPPORT_LIMIT = 128


def _pointer_value(content, pointer):
    """Read an already validated RFC 6901 pointer without interpreting its value."""
    current = content
    for segment in pointer.split('/')[1:]:
        part = segment.replace('~1', '/').replace('~0', '~')
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def _discovery_tasks(connection, key):
    # Discovery support locators record the question ID in occurrence.symbol.
    # Preserve unknowns instead of equating acceptance with complete context.
    rows = connection.execute(
        'SELECT DISTINCT o.symbol, COALESCE(t.status,\'unknown\') '
        'FROM discovery_support s JOIN observations v ON v.id=s.observation '
        'JOIN occurrences o ON o.id=v.occurrence LEFT JOIN tasks t ON t.id=o.symbol '
        'WHERE s.node=? ORDER BY 1', (key,)).fetchall()
    return dict(rows)


def _semantic_relation_evidence(items):
    projected = []
    for item in items[:SEMANTIC_EVIDENCE_LIMIT]:
        row = dict(item)
        limitation = row.get('limitation')
        if isinstance(limitation, str) and len(limitation.encode('utf-8')) > SEMANTIC_VALUE_LIMIT:
            row.pop('limitation')
            row['limitation_omitted'] = True
        projected.append(row)
    return projected


def semantic_context(connection, links, truncated, *, node_key, own=None, snapshot=None):
    """Project grounded fragments while retaining the discovery as their owner."""
    result = dict(status='not-linked', node_role_status='not-linked', entries=[], truncated=truncated, snapshot=snapshot,
                  basis='Fields describe the linked discovery and its scope, which may include an entire flow; '
                        'they are not automatically attributes of this node. Reviewed is limited to projected '
                        'answered investigations, not complete node behavior. Missing links do not prove absence.')
    associations = list(links)
    if own is not None:
        associations.insert(0, dict(key=own['key'], relation='self', direction='self',
                                    conditions=[], relation_id=None, evidence=[]))
    for link in associations:
        discovery = discovery_record(connection, link['key'], support_limit=SEMANTIC_SUPPORT_LIMIT)
        if discovery is None:
            continue
        content = discovery['content']
        fields = {}
        present = set(content).intersection(SEMANTIC_FIELDS) if isinstance(content, dict) else set()
        subject_present = isinstance(content, dict) and 'subject_node' in content
        subject = content.get('subject_node') if subject_present else None
        subject_support = []
        partial = set()
        fully_supported = set()
        fragments_truncated = set()
        value_truncated = False
        for support in discovery['support']:
            pointer = support['pointer']
            if subject_present and pointer in ('', '/subject_node'):
                subject_support.append(dict(pointer='/subject_node', support_pointer=pointer,
                                            evidence=support['evidence'][:SEMANTIC_EVIDENCE_LIMIT],
                                            evidence_truncated=len(support['evidence']) > SEMANTIC_EVIDENCE_LIMIT))
            if pointer == '':
                fragments = [('/' + field, field, content[field]) for field in SEMANTIC_FIELDS if field in present]
                fully_supported.update(present)
            else:
                top = pointer.split('/')[1].replace('~1', '/').replace('~0', '~')
                if top not in present:
                    continue
                fragments = [(pointer, top, _pointer_value(content, pointer))]
                if pointer != '/' + top:
                    partial.add(top)
                else:
                    fully_supported.add(top)
            for fragment_pointer, name, value in fragments:
                if len(fields.get(name, [])) >= SEMANTIC_FRAGMENTS_LIMIT:
                    fragments_truncated.add(name)
                    continue
                ref = dict(pointer=fragment_pointer, support_pointer=pointer,
                           evidence=support['evidence'][:SEMANTIC_EVIDENCE_LIMIT],
                           evidence_truncated=len(support['evidence']) > SEMANTIC_EVIDENCE_LIMIT)
                if len(canonical(value).encode('utf-8')) > SEMANTIC_VALUE_LIMIT:
                    ref['omitted'] = 'value exceeds projection limit; open discovery for full value'
                    value_truncated = True
                else:
                    ref['value'] = value
                fields.setdefault(name, []).append(ref)
        unsupported = sorted(present - fields.keys())
        if subject_present and (not isinstance(subject, str) or not subject_support):
            unsupported.append('subject_node')
        tasks = _discovery_tasks(connection, link['key'])
        additional_content = not isinstance(content, dict) or bool(set(content) - set(SEMANTIC_FIELDS) - {'subject_node'})
        subject_relation = ('shared' if not subject_present else 'unsupported'
                            if 'subject_node' in unsupported else 'same-node' if subject == node_key else 'other-node')
        role_supported = any(isinstance(item.get('value'), str) and item['value'].strip() and item['evidence']
                             for item in fields.get('role', []))
        field_scope = ('node' if subject_relation == 'same-node' and role_supported
                       and link['relation'] in {'describes', 'explained-by'} else 'discovery')
        title = discovery['title']
        title_truncated = len(title) > 160
        if title_truncated:
            title = title[:159] + '…'
        conditions_omitted = len(canonical(link['conditions']).encode('utf-8')) > SEMANTIC_VALUE_LIMIT
        subject_node_omitted = (subject_present and 'subject_node' not in unsupported and
                                len(subject.encode('utf-8')) > SEMANTIC_VALUE_LIMIT)
        relation_evidence = _semantic_relation_evidence(link['evidence'])
        entry = dict(discovery=link['key'], title=title, title_truncated=title_truncated, field_scope=field_scope,
                     subject_relation=subject_relation, subject_support=subject_support,
                     relationship=link['relation'], direction=link['direction'],
                     relation_id=link['relation_id'], conditions=None if conditions_omitted else link['conditions'],
                     conditions_omitted=conditions_omitted, relation_evidence=relation_evidence,
                     relation_evidence_truncated=len(link['evidence']) > SEMANTIC_EVIDENCE_LIMIT,
                     fields=fields, additional_content=additional_content,
                     support_truncated=discovery['support_truncated'],
                     fragments_truncated=sorted(fragments_truncated),
                     unsupported_fields=unsupported, partial_fields=sorted(partial - fully_supported),
                     subject_node_omitted=subject_node_omitted,
                     value_truncated=value_truncated, investigation_questions=sorted(tasks),
                     investigation_statuses=sorted(set(tasks.values())) or ['unknown'],
                     open=link['key'])
        if subject_present and 'subject_node' not in unsupported and not subject_node_omitted:
            entry['subject_node'] = subject
        result['entries'].append(entry)
    if result['entries']:
        def entry_incomplete(entry):
            return bool(
            entry['unsupported_fields'] or entry['partial_fields'] or entry['value_truncated']
            or entry['additional_content'] or not entry['fields'] or entry['support_truncated']
            or entry['fragments_truncated'] or entry['relation_evidence_truncated']
            or entry['title_truncated'] or entry['conditions_omitted'] or entry['subject_node_omitted']
            or any(item.get('limitation_omitted') for item in entry['relation_evidence'])
            or any(item['evidence_truncated'] for fragments in entry['fields'].values() for item in fragments)
            or any(item['evidence_truncated'] for item in entry['subject_support'])
            or (entry['subject_relation'] == 'same-node' and entry['field_scope'] != 'node')
            or any(status != 'answered' for status in entry['investigation_statuses'])
            or any(item.get('value') for name in ('gaps', 'limits')
                   for item in entry['fields'].get(name, [])))

        node_roles = [entry for entry in result['entries'] if entry['field_scope'] == 'node']
        role_candidates = [entry for entry in result['entries'] if entry['subject_relation'] == 'same-node']
        if node_roles:
            result['node_role_status'] = 'partial' if truncated or any(map(entry_incomplete, role_candidates)) else 'reviewed'
        incomplete = truncated or any(map(entry_incomplete, result['entries']))
        result['status'] = 'partial' if incomplete else 'reviewed'
    return result


def inspect_node(connection, selector):
    current = connection.execute('PRAGMA user_version').fetchone()[0] != 1
    result = []
    info = metadata(connection, 'snapshot', 'deferred_claims')
    snapshot = info.get('snapshot')
    for row in find_nodes(connection, selector):
        key = row['key']
        node = dict(row, evidence=evidence(connection, 'node_observations', 'node', key),
                    incoming=[edge_record(connection, item) for item in adjacent(connection, key, 'in', [])],
                    outgoing=[edge_record(connection, item) for item in adjacent(connection, key, 'out', [])],
                    incoming_candidates=[edge_record(connection, item) for item in incoming_candidates(connection, key)])
        discovery = discovery_record(connection, key) if current else None
        if discovery is not None:
            node['discovery'] = discovery
        context, truncated = related_discoveries(connection, key)
        node['related_discoveries'] = context
        node['related_discoveries_truncated'] = truncated
        node['context_status'] = 'self' if 'discovery' in node else 'linked' if context else 'not-linked'
        contextual, contextual_truncated = related_discoveries(connection, key, contextual_only=True)
        node['semantic_context'] = semantic_context(connection, contextual, contextual_truncated, node_key=key,
                                                    own=discovery, snapshot=snapshot)
        flows, flows_truncated = related_discoveries(connection, key, flows_only=True)
        node['flow_discoveries'] = semantic_context(connection, flows, flows_truncated, node_key=key)['entries']
        node['flow_discoveries_truncated'] = flows_truncated
        diagnostics = context_diagnostics(connection, node=key, limit=9)
        node['context_diagnostics'] = diagnostics[:8]
        node['context_diagnostics_truncated'] = len(diagnostics) > 8
        node['deferred_claims'] = [claim for claim in info.get('deferred_claims', [])
                                   if key in (claim['source'], claim['target'])]
        linked = sorted({item['key'] for item in (*context, *contextual, *flows)})
        node['reviewed_discrepancies'] = reviewed_discrepancies(connection, nodes=(key, *linked))
        questions = {item['symbol'] for item in node['evidence'] if item['profile'] == 'agent-investigation'}
        questions.update(item['symbol'] for link in (*contextual, *flows) for item in link['evidence'])
        questions.update(question for entry in (*node['semantic_context']['entries'], *node['flow_discoveries'])
                         for question in entry['investigation_questions'])
        questions.update(claim['question'] for claim in node['deferred_claims'])
        node['investigation_gaps'] = [dict(item, issues=json.loads(item['issues'])) for item in connection.execute(
            "SELECT c.area,c.status,c.reason,c.issues FROM coverage c JOIN tasks t ON t.id=c.task "
            "WHERE c.family='investigation' AND c.status!='analyzed' AND ("
            "EXISTS (SELECT 1 FROM json_each(t.report,'$.question.node_ids') WHERE value=?) OR "
            "(substr(?,1,5)='file:' AND EXISTS (SELECT 1 FROM json_each(t.report,'$.question.seeds') "
            "WHERE value=substr(?,6))) OR EXISTS (SELECT 1 FROM json_each(?) WHERE value=c.area)) "
            "ORDER BY c.area LIMIT 13", (key, key, key, canonical(sorted(questions))))]
        node['investigation_gaps_truncated'] = len(node['investigation_gaps']) > 12
        node['investigation_gaps'] = node['investigation_gaps'][:12]
        result.append(node)
    return result


def trace(connection, selector, direction, types, depth, max_nodes, max_edges, *, summary=False):
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
    info = metadata(connection, 'snapshot', 'status', 'investigation_scope', 'profile',
                    'multidimensional_profile')
    question_scope = info.get('investigation_scope')
    relevant, reached_areas, reached_paths = set(), set(), set()
    multidimensional = (info.get('profile', {}).get('name') == 'multidimensional-static' or
                        'multidimensional_profile' in info)
    for key in nodes:
        for (path,) in connection.execute(
            'SELECT DISTINCT o.path FROM node_observations n JOIN observations v ON n.observation=v.id '
            'JOIN occurrences o ON v.occurrence=o.id WHERE n.node=?', (key,)
        ):
            reached_paths.add(path)
            reached_areas.add(path.split('/', 1)[0] if '/' in path else '.')
    if question_scope is None:
        profile = info['profile']
        relevant = {family for family, kinds in profile['edge_types'].items()
                    if not types or set(types).intersection(kinds)}
    # Open questions may identify bridges beyond the evidence already reached.
    coverage_filter = (" FROM coverage WHERE status NOT IN ('analyzed','inapplicable','excluded') "
                       "AND (family='investigation' "
                       "OR (family IN (SELECT value FROM json_each(?)) AND area IN (SELECT value FROM json_each(?))) "
                       "OR (family IN ('multidimensional-static','python-static') "
                       "AND area IN (SELECT value FROM json_each(?))))")
    columns = 'family,status,COUNT(*) AS count' if summary else 'area,family,status,reason'
    order = ' GROUP BY family,status ORDER BY family,status' if summary else ' ORDER BY area,family'
    params = (canonical(sorted(relevant)), canonical(sorted(reached_areas)),
              canonical(sorted(reached_paths) if multidimensional else []))
    gaps = [dict(row) for row in connection.execute('SELECT ' + columns + coverage_filter + order, params)]
    coverage_key = 'coverage_frontier_summary' if summary else 'coverage_frontier'
    scope = {'investigation_scope': question_scope} if question_scope is not None else {'repository_status': info['status']}
    return dict(snapshot=info['snapshot'], status=info['status'], **scope, seeds=seeds[:max_nodes], nodes=sorted(nodes),
                edges=[edge_record(connection, row) for _, row in sorted(edges.items())],
                truncated=bool(limits), limits=sorted(limits), analysis_incomplete=bool(gaps or unresolved),
                **{coverage_key: gaps},
                unresolved_frontier=[edge_record(connection, row) for _, row in sorted(unresolved.items())])
