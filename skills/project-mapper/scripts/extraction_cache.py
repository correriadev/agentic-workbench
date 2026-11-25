"""Store snapshot-bound, file-local facts for the next static extraction."""

from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys

from scan_files import canonical, digest


APPLICATION_ID = 0x504D4348
VERSION = 1


def extractor_identity(profile):
    directory = Path(__file__).resolve().parent
    sources = ('extraction_cache.py', 'python_profile.py', 'multidimensional.py',
               'csharp_profile.py', 'scan_files.py', 'resolve.py')
    revisions = [sha256((directory / name).read_bytes()).hexdigest() for name in sources]
    return digest([VERSION, profile, list(sys.version_info), revisions])


def read_cache(path, snapshot, identity):
    """Return ownership and matching entries. The published graph is authoritative."""
    if not path.exists():
        return True, None
    owned = False
    try:
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
            db.execute('PRAGMA trusted_schema=OFF')
            owned = db.execute('PRAGMA application_id').fetchone()[0] == APPLICATION_ID
            if not owned or db.execute('PRAGMA user_version').fetchone()[0] != VERSION:
                return owned, None
            header = db.execute('SELECT snapshot, extractor FROM header').fetchall()
            if header != [(snapshot, identity)] or db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                return owned, None
            return owned, {path: (key, payload, fingerprint) for path, key, payload, fingerprint in
                           db.execute('SELECT path, key, payload, fingerprint FROM extracts')}
    except sqlite3.Error:
        return owned, None


class ExtractionCache:
    def __init__(self, identity, previous=None, changed=()):
        self.identity = identity
        self.previous = previous or {}
        self.changed = set(changed)
        self.entries = {}
        self.reused = set()
        self.extracted = set()

    def extract(self, path, content_id, kind, compute):
        key = digest([path, content_id, kind])
        previous = self.previous.get(path)
        if path not in self.changed and previous and previous[0] == key:
            _, payload, fingerprint = previous
            if sha256(payload.encode()).hexdigest() == fingerprint:
                try:
                    value = json.loads(payload)
                except (ValueError, RecursionError):
                    pass
                else:
                    if isinstance(value, dict):
                        self.entries[path] = previous
                        self.reused.add(path)
                        return value
        value = compute()
        payload = canonical(value)
        self.entries[path] = (key, payload, sha256(payload.encode()).hexdigest())
        self.extracted.add(path)
        return value

    def write(self, path, snapshot):
        with path.open('xb'):
            pass
        with closing(sqlite3.connect(path)) as db, db:
            db.execute(f'PRAGMA application_id={APPLICATION_ID}')
            db.execute(f'PRAGMA user_version={VERSION}')
            db.execute('CREATE TABLE header(snapshot TEXT, extractor TEXT) STRICT')
            db.execute('CREATE TABLE extracts(path TEXT PRIMARY KEY, key TEXT, payload TEXT, fingerprint TEXT) STRICT')
            db.execute('INSERT INTO header VALUES (?, ?)', (snapshot, self.identity))
            db.executemany('INSERT INTO extracts VALUES (?, ?, ?, ?)',
                           ((path, *entry) for path, entry in sorted(self.entries.items())))


def pack_graph(graph):
    """Encode file-local graph facts without source text or lexer tokens."""
    return dict(nodes=graph.nodes, occurrences=graph.occurrences, observations=graph.observations,
                provenance=graph.provenance, node_observations=sorted(graph.node_observations),
                relationships={key: dict(item, evidence=sorted(item['evidence']))
                               for key, item in graph.relationships.items()},
                memberships=[(key, sorted(evidence)) for key, evidence in sorted(graph.memberships.items())])


def merge_graph(graph, fragment):
    for name in ('nodes', 'occurrences', 'observations', 'provenance'):
        getattr(graph, name).update(fragment[name])
    graph.node_observations.update(tuple(pair) for pair in fragment['node_observations'])
    for key, item in fragment['relationships'].items():
        graph.relationships.setdefault(key, dict(item, evidence=set()))['evidence'].update(item['evidence'])
    for key, evidence in fragment['memberships']:
        graph.memberships.setdefault(tuple(key), set()).update(evidence)
