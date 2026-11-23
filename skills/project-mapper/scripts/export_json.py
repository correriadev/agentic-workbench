"""Stream a JSON snapshot of the published graph without modifying it."""

import json

from scan_files import MappingError


TABLES = ('inventory', 'nodes', 'occurrences', 'provenance', 'observations',
          'node_observations', 'relationships', 'relationship_candidates',
          'relationship_observations', 'memberships', 'membership_observations',
          'tasks', 'coverage', 'discrepancies', 'discrepancy_observations',
          'discoveries', 'discovery_support', 'discovery_terms')
JSON_COLUMNS = {'occurrences': {'span'}, 'relationships': {'conditions'},
                'tasks': {'report'}, 'coverage': {'paths', 'method', 'issues'},
                'discoveries': {'terms', 'content'}}


def prepare_dimension(db, dimension):
    db.execute('CREATE TEMP TABLE export_selected (key TEXT PRIMARY KEY) WITHOUT ROWID')
    db.execute('INSERT INTO export_selected SELECT DISTINCT node FROM memberships WHERE dimension=?', (dimension,))
    if not db.execute('SELECT 1 FROM export_selected LIMIT 1').fetchone():
        raise MappingError('dimension has no memberships in the published graph')
    db.execute('CREATE TEMP TABLE export_edges (id TEXT PRIMARY KEY) WITHOUT ROWID')
    db.execute('INSERT INTO export_edges SELECT id FROM relationships WHERE source IN export_selected OR target IN export_selected')
    db.execute('CREATE TEMP TABLE export_nodes (key TEXT PRIMARY KEY) WITHOUT ROWID')
    db.execute('INSERT OR IGNORE INTO export_nodes SELECT key FROM export_selected')
    db.execute('INSERT OR IGNORE INTO export_nodes SELECT source FROM relationships WHERE id IN export_edges')
    db.execute('INSERT OR IGNORE INTO export_nodes SELECT target FROM relationships WHERE id IN export_edges AND target IS NOT NULL')
    db.execute('INSERT OR IGNORE INTO export_nodes SELECT node FROM relationship_candidates WHERE relationship IN export_edges')
    db.execute('CREATE TEMP TABLE export_members (id TEXT PRIMARY KEY) WITHOUT ROWID')
    db.execute('INSERT INTO export_members SELECT id FROM memberships WHERE node IN export_nodes')
    db.execute('CREATE TEMP TABLE export_observations (id TEXT PRIMARY KEY) WITHOUT ROWID')
    db.execute('INSERT OR IGNORE INTO export_observations SELECT observation FROM node_observations WHERE node IN export_nodes')
    db.execute('INSERT OR IGNORE INTO export_observations SELECT observation FROM relationship_observations WHERE relationship IN export_edges')
    db.execute('INSERT OR IGNORE INTO export_observations SELECT observation FROM membership_observations WHERE membership IN export_members')
    db.execute('INSERT OR IGNORE INTO export_observations SELECT observation FROM discrepancy_observations')
    if db.execute('PRAGMA user_version').fetchone()[0] >= 2:
        db.execute('INSERT OR IGNORE INTO export_observations SELECT observation FROM discovery_support WHERE node IN export_nodes')


FILTERS = {
    'nodes': 'key IN export_nodes',
    'node_observations': 'node IN export_nodes',
    'relationships': 'id IN export_edges',
    'relationship_candidates': 'relationship IN export_edges',
    'relationship_observations': 'relationship IN export_edges',
    'memberships': 'id IN export_members',
    'membership_observations': 'membership IN export_members',
    'observations': 'id IN export_observations',
    'occurrences': 'id IN (SELECT occurrence FROM observations WHERE id IN export_observations)',
    'provenance': 'id IN (SELECT context FROM observations WHERE id IN export_observations)',
    'discoveries': 'node IN export_nodes',
    'discovery_support': 'node IN export_nodes',
    'discovery_terms': 'node IN export_nodes',
}


def write_export(db, output, *, dimension=None):
    if dimension is not None:
        prepare_dimension(db, dimension)
    version = db.execute('PRAGMA user_version').fetchone()[0]
    metadata = {key: json.loads(value) for key, value in db.execute('SELECT key,value FROM metadata ORDER BY key')}
    selection = dict(mode='dimension' if dimension else 'full', dimension=dimension,
                     scope='One-hop edges and their endpoints; inventory, coverage, tasks and discrepancies are global.'
                     if dimension else 'All persisted tables.')
    output.write('{"format":"project-mapper-json-v1","schema_version":')
    output.write(json.dumps(version))
    output.write(',"selection":' + json.dumps(selection, ensure_ascii=False))
    output.write(',"metadata":' + json.dumps(metadata, ensure_ascii=False, allow_nan=False))
    output.write(',"tables":{')
    counts = {}
    tables = TABLES if version >= 2 else TABLES[:-3]
    for index, table in enumerate(tables):
        if index:
            output.write(',')
        output.write(json.dumps(table) + ':[')
        where = ' WHERE ' + FILTERS[table] if dimension and table in FILTERS else ''
        columns = [row[1] for row in db.execute('PRAGMA table_info(' + table + ')')]
        # Deterministic ordering avoids relying on SQLite's physical layout.
        query = 'SELECT * FROM ' + table + where + ' ORDER BY ' + ','.join('"' + c + '"' for c in columns)
        count = 0
        for raw in db.execute(query):
            row = dict(raw)
            for column in JSON_COLUMNS.get(table, set()):
                row[column] = json.loads(row[column])
            if count:
                output.write(',')
            output.write(json.dumps(row, ensure_ascii=False, allow_nan=False, separators=(',', ':')))
            count += 1
        output.write(']')
        counts[table] = count
    output.write('}}\n')
    return counts
