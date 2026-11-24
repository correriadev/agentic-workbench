from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import unittest

from test_acceptance import test_directory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import graph_store as store
from scan_files import MappingError


class DiscoveryStore(unittest.TestCase):
    def test_legacy_replay_and_exact_key_precedence(self):
        nodes = [('service:api', 'service', '', 'api', 0), ('alias:other', 'alias', '', 'service:api', 0)]
        with closing(sqlite3.connect(':memory:')) as db:
            db.row_factory = sqlite3.Row
            db.executescript(store.SCHEMA_V1)
            db.execute('PRAGMA user_version=1')
            db.execute("INSERT INTO metadata VALUES ('schema_version','1')")
            db.executemany('INSERT INTO nodes VALUES (?,?,?,?,?)', nodes)
            expected = dict(metadata=[('schema_version', '2')], nodes=nodes, discoveries=[], discovery_support=[])
            store.check_integrity(db, expected)
            row, = store.inspect_node(db, 'service:api')
            self.assertEqual(row['key'], 'service:api')
            self.assertEqual(row['context_diagnostics'], [])
            self.assertEqual(row['flow_discoveries'], [])
            self.assertEqual(row['reviewed_discrepancies'], [])
            self.assertEqual(store.search_discoveries(db, 'api', 3), [])
            with self.assertRaisesRegex(MappingError, 'discovery'):
                store.open_discovery(db, 'service:api')

    def test_search_indexes_routes_and_only_open_returns_content(self):
        discoveries = [('r/1', 'Café retention policy', 'Object lifetimes', '["physical collection"]', 'null'),
                       ('r/2', 'Archive', 'Retention reference', '[]', '{"huge":"not-searchable"}')]
        nodes = [(key, 'discovery', '', title, 0) for key, title, *_ in discoveries]
        data = dict(nodes=nodes, inventory=[('rule.py', 'file', 'abc', 1, 1, 'cited', '', None)],
                    occurrences=[('o', 'rule.py', 'abc', '[1,0,1,5]', 'source-range', 'q', 'hash')],
                    provenance=[('p', 'agent-investigation', 1, 'reading')],
                    observations=[('v', 'o', 'p', 'code', 'source', '')], discoveries=discoveries,
                    discovery_support=[('r/1', '', 'v'), ('r/2', '/huge', 'v')])
        with test_directory() as work:
            path = work / 'map.sqlite'
            store.write(path, data)
            with store.database(path) as db:
                selected = set()

                def audit_read(action, table, column, unused_db, unused_view):
                    if action == sqlite3.SQLITE_READ:
                        selected.add((table, column))
                    return sqlite3.SQLITE_OK

                db.set_authorizer(audit_read)
                hits = store.search_discoveries(db, 'CAFE and RETENTION', 1)
                self.assertEqual(hits, [dict(key='r/1', title=discoveries[0][1], summary=discoveries[0][2])])
                self.assertNotIn(('discoveries', 'content'), selected)
                self.assertEqual(store.search_discoveries(db, 'not-searchable', 4), [])
                opened = store.open_discovery(db, 'r/1')
                self.assertIsNone(opened['content'])
                self.assertEqual(opened['support'][0]['pointer'], '')
                self.assertEqual(opened['support'][0]['evidence'][0]['path'], 'rule.py')
            with closing(sqlite3.connect(path)) as db:
                db.execute("DELETE FROM discovery_terms WHERE term='cafe'")
                with self.assertRaisesRegex(MappingError, 'discovery_terms'):
                    store.check_integrity(db, data)

    def test_search_ranks_exact_source_context_before_mentions(self):
        discoveries = [
            ('details', 'Write boundary', 'Persists the request and queue record.', '["acceptance"]', 'null'),
            ('mention', 'RecordRequest', 'Mentions RecordRequest in another handler.', '[]', 'null'),
            ('read-boundary', 'Receipt lookup', 'Reads the receipt with a resolver.', '["lookup"]', 'null'),
        ]
        path = 'src/nested/RecordRequest.cs'
        key = f'file:{path}'
        other_path = 'src/other/RecordRequest.cs'
        other_key = f'file:{other_path}'
        case_variant = 'src/nested/recordrequest.cs'
        case_key = f'file:{case_variant}'
        nodes = [(item, 'discovery', '', title, 0) for item, title, *_ in discoveries]
        nodes.extend((f'file:{name}', 'file', 'repository', name, 0) for name in (path, other_path, case_variant))
        relations = [
            ('r1', 'describes', 'semantic', 'details', key, 'resolved', '[]', '', ''),
            ('r2', 'explained-by', 'semantic', key, 'details', 'resolved', '[]', '', ''),
            ('r3', 'explained-by', 'semantic', other_key, 'read-boundary', 'resolved', '[]', '', ''),
            ('r4', 'describes', 'semantic', 'read-boundary', case_key, 'resolved', '[]', '', ''),
        ]
        with closing(sqlite3.connect(':memory:')) as db:
            db.row_factory = sqlite3.Row
            db.executescript(store.SCHEMA)
            db.execute('PRAGMA user_version=2')
            db.executemany('INSERT INTO nodes VALUES (?,?,?,?,?)', nodes)
            db.executemany('INSERT INTO discoveries VALUES (?,?,?,?,?)', discoveries)
            db.executemany('INSERT INTO discovery_terms VALUES (?,?,?)', store.search_rows(discoveries))
            db.executemany('INSERT INTO relationships VALUES (?,?,?,?,?,?,?,?,?)', relations)
            for selector in (key, path, 'RecordRequest.cs', 'RecordRequest'):
                with self.subTest(selector=selector):
                    self.assertEqual(store.search_discoveries(db, selector, 1)[0]['key'], 'details')
            self.assertEqual([r['key'] for r in store.search_discoveries(db, 'RecordRequest', 5)],
                             ['details', 'read-boundary', 'mention'])
            self.assertEqual(store.search_discoveries(db, 'RecordRequest', 1, terms='receipt resolver')[0]['key'],
                             'read-boundary')
            self.assertEqual(store.search_discoveries(db, key, 1, terms='receipt resolver')[0]['key'], 'details')
            self.assertEqual(store.search_discoveries(db, path, 1, terms='receipt resolver')[0]['key'], 'details')
            self.assertEqual(store.search_discoveries(db, 'Onde a requisição é gravada?', 1,
                                                     terms='acceptance queue')[0]['key'], 'details')
            self.assertEqual(store.search_discoveries(db, 'mention', 1, terms='acceptance')[0]['key'], 'mention')


if __name__ == '__main__':
    unittest.main()
