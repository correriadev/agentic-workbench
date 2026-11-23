"""Behavioral checks for the snapshot-backed multidimensional profile."""

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from multidimensional import extract_graph, javascript_candidates, tokens, PROFILE
from python_profile import Source
from resolve import Graph


class Reader:
    def __init__(self, files):
        self.files = {path: text.encode() for path, text in files.items()}
        self.entries = {path: dict(path=path, kind='file', eligible=True, tracked=True,
                                  content_id='sha256:' + hashlib.sha256(data).hexdigest())
                        for path, data in self.files.items()}

    def read(self, path):
        return self.files[path]


class MultidimensionalTest(unittest.TestCase):
    def graph(self, files):
        reader = Reader(files)
        return extract_graph(dict(entries=list(reader.entries.values())), reader)

    def test_js_imports_resolve_nodenext_and_ignore_comments_and_strings(self):
        graph, coverage, outcomes, _ = self.graph({
            'src/main.ts': '''// import "./fake.js"\nconst s = "import './fake.js'";\nimport { run } from "./service.js";\nconst m = import("./service.js");\n''',
            'src/service.ts': 'export const run = () => 1;\n',
            'src/fake.ts': 'export const fake = 1;\n',
        })
        links = list(graph.relationships.values())
        imports = [r for r in links if r['type'] == 'imports']
        self.assertEqual({r['target'] for r in imports}, {'file:src/service.ts'})
        self.assertTrue(all(r['state'] == 'resolved' for r in imports))
        self.assertEqual(outcomes['src/main.ts']['status'], 'partial')
        self.assertTrue(any(row['area'] == 'src/main.ts' for row in coverage))

    def test_unresolved_import_and_package_entry_point(self):
        graph, _, _, _ = self.graph({
            'package.json': '{"name":"example","bin":{"rea":"scripts/rea.mjs"}}',
            'scripts/rea.mjs': 'import "./missing.js";\n',
        })
        links = list(graph.relationships.values())
        self.assertTrue(any(r['type'] == 'registers' and r['target'] == 'file:scripts/rea.mjs'
                            for r in links))
        self.assertTrue(any(r['type'] == 'imports' and r['state'] == 'unresolved'
                            for r in links))

    def test_wrangler_binding_and_test_membership(self):
        graph, _, _, _ = self.graph({
            'website/wrangler.toml': 'main = "worker.mjs"\n[assets]\nbinding = "ASSETS"\n',
            'website/worker.mjs': 'export default {};\n',
            'website/worker.test.mjs': 'import worker from "./worker.mjs";\n',
        })
        links = list(graph.relationships.values())
        self.assertTrue(any(r['type'] == 'configures-entry' and r['target'] == 'file:website/worker.mjs'
                            for r in links))
        self.assertTrue(any(m[0] == 'test' and m[2] == 'file:website/worker.test.mjs'
                            for m in graph.memberships))

    def test_config_values_are_not_serialized_into_graph(self):
        secret = 'sensitive-credential-value-29835'
        graph, _, _, _ = self.graph({
            'package.json': '{"name":"example","scripts":{"test":"TOKEN=' + secret + ' node run.js"}}',
        })
        self.assertNotIn(secret, repr(vars(graph)))

    def test_tool_symbols_and_config_are_candidates_with_source_evidence(self):
        graph, _, _, _ = self.graph({
            'src/server/tools.ts': '''export const bindTools = () => ({
                analyze_javascript_application: {
                    run: () => process.env.REA_ASAR_MAX_LISTING_BYTES,
                },
            });
            const text = "not_real_tool: { run: () => 2 }";
            // unused_tool: { run: () => 3 }
            ''',
        })
        names = {item['name'] for item in graph.nodes.values()}
        self.assertIn('bindTools', names)
        self.assertIn('analyze_javascript_application', names)
        self.assertIn('REA_ASAR_MAX_LISTING_BYTES', names)
        self.assertNotIn('not_real_tool', names)
        self.assertNotIn('unused_tool', names)
        for key, value in graph.nodes.items():
            if value['name'] in {'bindTools', 'analyze_javascript_application', 'REA_ASAR_MAX_LISTING_BYTES'}:
                evidence = [graph.observations[observation] for node, observation in graph.node_observations if node == key]
                self.assertTrue(evidence)
                self.assertTrue(all(item['authority'] == 'candidate' for item in evidence))

    def test_candidates_are_not_specific_to_rea_and_coverage_counts_relations(self):
        graph, coverage, _, _ = self.graph({
            'app/bindings.ts': '''export const definitions = {
              calculate_total: { run: () => process.env.API_ENDPOINT },
              refresh_index: { run: () => process.env['API_TOKEN'] },
            };''',
        })
        names = {item['name'] for item in graph.nodes.values()}
        self.assertTrue({'calculate_total', 'refresh_index', 'API_ENDPOINT', 'API_TOKEN'} <= names)
        row = next(item for item in coverage if item['area'] == 'app/bindings.ts')
        self.assertGreater(row['findings'], 0)

    def test_nested_object_candidate_scan_has_linear_token_access(self):
        # Count accesses instead of imposing a wall-clock threshold on test machines.
        class CountingTokens(list):
            accesses = 0

            def __getitem__(self, key):
                value = super().__getitem__(key)
                self.accesses += len(value) if isinstance(key, slice) else 1
                return value

        text = 'outer_key: {' * 2000 + 'run: handler' + '}' * 2000
        reader = Reader({'app/test.ts': text})
        sequence = CountingTokens(tokens(text))
        javascript_candidates(Graph(PROFILE), Source(reader, 'app/test.ts'), sequence)
        self.assertLess(sequence.accesses, 20 * len(sequence))

    def test_submodule_boundary_is_visible_without_reading_its_contents(self):
        reader = Reader({'app/index.ts': 'export const a = 1;'})
        boundary = dict(path='third_party/a', kind='submodule', content_id='git:' + 'a' * 40,
                        eligible=False, tracked=True, status='unsupported', reason='submodule boundary')
        entries = [*reader.entries.values(), boundary]
        graph, coverage, _, _ = extract_graph(dict(entries=entries), reader)
        self.assertIn('boundary:third_party/a', graph.nodes)
        self.assertEqual(graph.nodes['boundary:third_party/a']['kind'], 'submodule')
        record = next(row for row in coverage if row['area'] == 'third_party/a')
        self.assertEqual(record['status'], 'unsupported')
        self.assertEqual(record['reason'], 'submodule boundary')
        self.assertEqual(record['findings'], 0)

    def test_optional_chaining_config_candidates(self):
        graph, _, _, _ = self.graph({
            'app/config.ts': '''
              let first = options.environment?.REA_ASAR_MAX_LISTING_BYTES;
              let second = options.config?.['SERVICE_URL'];
            ''',
        })
        names = {item['name'] for item in graph.nodes.values()}
        self.assertIn('REA_ASAR_MAX_LISTING_BYTES', names)
        self.assertIn('SERVICE_URL', names)


if __name__ == '__main__':
    unittest.main()
