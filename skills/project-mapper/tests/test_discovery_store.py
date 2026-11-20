from contextlib import closing
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest

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
            self.assertEqual([row['key'] for row in store.inspect_node(db, 'service:api')], ['service:api'])
            self.assertEqual(store.search_discoveries(db, 'api', 3), [])
            with self.assertRaisesRegex(MappingError, 'discovery'):
                store.open_discovery(db, 'service:api')

    def test_search_indexes_routes_and_only_open_returns_content(self):
        discoveries = [('r/1', 'Política de retenção', 'Prazos do objeto', '["recolha física"]', 'null'),
                       ('r/2', 'Arquivo', 'Referência de retenção', '[]', '{"huge":"not-searchable"}')]
        nodes = [(key, 'discovery', '', title, 0) for key, title, *_ in discoveries]
        data = dict(nodes=nodes, inventory=[('rule.py', 'file', 'abc', 1, 1, 'cited', '', None)],
                    occurrences=[('o', 'rule.py', 'abc', '[1,0,1,5]', 'source-range', 'q', 'hash')],
                    provenance=[('p', 'agent-investigation', 1, 'reading')],
                    observations=[('v', 'o', 'p', 'code', 'source', '')], discoveries=discoveries,
                    discovery_support=[('r/1', '', 'v'), ('r/2', '/huge', 'v')])
        with TemporaryDirectory() as work:
            path = Path(work) / 'map.sqlite'
            store.write(path, data)
            with store.database(path) as db:
                selected = set()

                def audit_read(action, table, column, unused_db, unused_view):
                    if action == sqlite3.SQLITE_READ:
                        selected.add((table, column))
                    return sqlite3.SQLITE_OK

                db.set_authorizer(audit_read)
                hits = store.search_discoveries(db, 'RECOLHA e RETENCAO', 1)
                self.assertEqual(hits, [dict(key='r/1', title=discoveries[0][1], summary=discoveries[0][2])])
                self.assertNotIn(('discoveries', 'content'), selected)
                self.assertEqual(store.search_discoveries(db, 'not-searchable', 4), [])
                opened = store.open_discovery(db, 'r/1')
                self.assertIsNone(opened['content'])
                self.assertEqual(opened['support'][0]['pointer'], '')
                self.assertEqual(opened['support'][0]['evidence'][0]['path'], 'rule.py')
            with closing(sqlite3.connect(path)) as db:
                db.execute("DELETE FROM discovery_terms WHERE term='recolha'")
                with self.assertRaisesRegex(MappingError, 'discovery_terms'):
                    store.check_integrity(db, data)


if __name__ == '__main__':
    unittest.main()
