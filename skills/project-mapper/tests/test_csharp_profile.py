"""Source-backed .NET mapping and conservative candidate checks."""
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from multidimensional import extract_graph
from test_acceptance import fixture, git, invoke, rows, test_directory
from test_investigation import add_question, accept, publish_investigation, save


class Reader:
    def __init__(self, files):
        self.files = {path: text.encode() for path, text in files.items()}
        self.entries = {path: dict(path=path, kind='file', eligible=True, tracked=True,
                                  content_id='sha256:' + hashlib.sha256(data).hexdigest())
                        for path, data in self.files.items()}

    def read(self, path):
        return self.files[path]


@unittest.skipUnless(importlib.util.find_spec('tree_sitter') and importlib.util.find_spec('tree_sitter_c_sharp'),
                     'optional C# parser dependencies are not installed')
class CSharpProfileTest(unittest.TestCase):
    def setUp(self):
        self.assertIn('csharp', inspect.signature(extract_graph).parameters,
                      'multidimensional extraction must support the C# profile')

    def test_csharp_declarations_candidates_and_project(self):
        reader = Reader({'src/Api/Api.csproj': '<Project><ItemGroup><ProjectReference Include="../Core/Core.csproj" /></ItemGroup></Project>',
                         'src/Core/Core.csproj': '<Project />',
                         'src/Api/Controller.cs': '''namespace Example.Api;
// class NotAClass { }
[Route("api/items")]
public class Controller {
  public Controller(IRepository repo) { }
  [HttpPost("send")] public void Send(string x) { repo.Save(x); }
  [Fact] public void TestSend() { }
}
''',
                         'src/Api/Program.cs': 'services.AddScoped<IRepository, Repository>();\napp.MapGet("/health", Handler);'})
        graph, coverage, outcomes, _ = extract_graph(dict(entries=list(reader.entries.values())), reader, csharp=True)
        names = {node['name'] for node in graph.nodes.values()}
        self.assertTrue({'Controller', 'Send', 'TestSend', 'IRepository', 'Repository'} <= names)
        self.assertIn('HttpPost send', names)
        self.assertIn('MapGet /health', names)
        self.assertIn('Route api/items', names)
        self.assertNotIn('NotAClass', names)
        self.assertEqual(outcomes['src/Api/Controller.cs']['status'], 'partial')
        types = {edge['type'] for edge in graph.relationships.values()}
        self.assertTrue({'contains', 'calls', 'registers', 'declares-endpoint', 'references-project'} <= types)
        calls = [edge for edge in graph.relationships.values() if edge['type'] == 'calls']
        self.assertTrue(calls and all(edge['state'] == 'unresolved' for edge in calls))
        self.assertTrue(any(key[0] == 'test' for key in graph.memberships))
        self.assertTrue(all(edge['evidence'] for edge in graph.relationships.values()))

    def test_syntax_errors_are_partial_and_no_literal_secrets(self):
        secret = 'password-super-secret-74643'
        reader = Reader({'Secrets.cs': 'class C { string x = "' + secret + '"; void M( { }'})
        graph, _, outcomes, _ = extract_graph(dict(entries=list(reader.entries.values())), reader, csharp=True)
        self.assertEqual(outcomes['Secrets.cs']['status'], 'partial')
        self.assertIn('syntax', outcomes['Secrets.cs']['reason'].lower())
        self.assertNotIn(secret, repr(vars(graph)))

    def test_published_csharp_map_and_semantic_investigation_replay(self):
        with test_directory() as repo:
            revision = fixture(repo, {'Api.csproj': '<Project />',
                                      'Api.cs': 'namespace App; public class Api { public void Go() {} }\n'})
            invoke(repo, 'map', '--commit', revision, '--csharp')
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

            self.assertTrue(invoke(repo, 'search', 'Api')['nodes'])
            run = invoke(repo, 'investigate', '--commit', revision, '--from-graph')
            summary = invoke(repo, 'check-plan', run['run'], '--summary')
            self.assertGreater(summary['assigned_nodes'], 0)
            plan = json.loads(Path(run['plan']).read_text(encoding='utf-8'))
            question = next(q for q in plan['questions'] if 'Api.cs' in q['seeds'])
            type_key = next(n for n in question['node_ids'] if n.startswith('csharp-type:'))
            page = invoke(repo, 'read-input', run['run'], question['id'], 'Api.cs', '--count', '1')
            anchor = dict(path='Api.cs', content_id=page['content_id'], start=1, end=1)
            save(Path(run['shards']) / (question['id'] + '.json'), dict(
                snapshot=run['snapshot']['identity'], question=question['id'], status='partial', gap='Flow remains open.',
                claims=[dict(source=type_key, relation='describes', target='component:api', condition='', evidence=[anchor])]))
            accept(repo, run, question['id'])
            publish_investigation(repo, run)
            node = invoke(repo, 'node', type_key)['nodes'][0]
            self.assertEqual(node['kind'], 'class')
            self.assertTrue(any(edge['type'] == 'describes' for edge in node['outgoing']))
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

    def test_refresh_reuses_csharp_and_rebinds_project_candidates(self):
        repo = self.enterContext(test_directory())
        revision = fixture(repo, {'src/Api.cs': 'namespace App; public class Api { public void Go() {} }\n',
                                  'App.csproj': '<Project />'})
        invoke(repo, 'map', '--commit', revision, '--csharp')
        git(repo, 'mv', 'App.csproj', 'src/Api.csproj')
        git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test',
            '-c', 'commit.gpgsign=false', 'commit', '-qm', 'move project')
        result = invoke(repo, 'refresh', '--commit', 'HEAD')
        self.assertEqual((result['mode'], result['reused_files'], result['extracted_files']),
                         ('incremental', 1, 1))
        self.assertEqual(rows(repo, 'SELECT c.node FROM relationship_candidates c '
                                    'JOIN relationships r ON r.id=c.relationship '
                                    "WHERE r.type='belongs-to-project' AND r.source='file:src/Api.cs'"),
                         [('dotnet-project:src/Api.csproj',)])
        self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

    def test_import_preserves_source_and_replays_reviewed_shards_in_separate_checkout(self):
        with test_directory() as source, test_directory() as target:
            revision = fixture(source, {'Api.cs': 'namespace App; public class Api { public void Go() {} }\n'})
            invoke(source, 'map', '--commit', revision)
            run = invoke(source, 'investigate', '--commit', revision, '--from-graph')
            plan = json.loads(Path(run['plan']).read_text(encoding='utf-8'))
            question = next(q for q in plan['questions'] if 'Api.cs' in q['seeds'])
            page = invoke(source, 'read-input', run['run'], question['id'], 'Api.cs', '--count', '1')
            anchor = dict(path='Api.cs', content_id=page['content_id'], start=1, end=1)
            save(Path(run['shards']) / (question['id'] + '.json'), dict(
                snapshot=run['snapshot']['identity'], question=question['id'], status='partial', gap='Flow remains open.',
                claims=[dict(source='file:Api.cs', relation='describes', target='component:api', condition='', evidence=[anchor])]))
            accept(source, run, question['id'])
            publish_investigation(source, run)
            original_graph = (source / '.project-mapper/graph.sqlite').read_bytes()
            subprocess.run(['git', 'clone', '-q', str(source), str(target)], check=True)
            invoke(target, 'map', '--commit', revision, '--csharp')
            decisions_path = Path(run['decisions'])
            decisions = json.loads(decisions_path.read_text(encoding='utf-8'))
            save(decisions_path, {question['id']: 'invalid-fingerprint'})
            rejected = invoke(target, 'import-run', '--source-repo', str(source), '--source-run', run['run'], ok=False)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn('stale or missing accepted shard', rejected.stderr)
            save(decisions_path, decisions)
            imported = invoke(target, 'import-run', '--source-repo', str(source), '--source-run', run['run'])
            self.assertEqual(imported['accepted'], 1)
            self.assertGreater(imported['added_questions'], 0)
            self.assertEqual((source / '.project-mapper/graph.sqlite').read_bytes(), original_graph)
            publish_investigation(target, imported)
            self.assertEqual(invoke(target, 'verify')['integrity'], 'ok')
            self.assertTrue(any(edge['type'] == 'describes' for edge in invoke(target, 'node', 'file:Api.cs')['nodes'][0]['outgoing']))

    def test_mismatched_snapshot_does_not_replace_target_graph(self):
        with test_directory() as source, test_directory() as target:
            revision = fixture(source, {'Api.cs': 'class One {}\n'})
            invoke(source, 'map', '--commit', revision)
            run = invoke(source, 'investigate', '--commit', revision, '--from-graph')
            revision2 = fixture(target, {'Api.cs': 'class Other {}\n'})
            invoke(target, 'map', '--commit', revision2, '--csharp')
            graph = (target / '.project-mapper/graph.sqlite').read_bytes()
            result = invoke(target, 'import-run', '--source-repo', str(source), '--source-run', run['run'], ok=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((target / '.project-mapper/graph.sqlite').read_bytes(), graph)


class CSharpDependencyTest(unittest.TestCase):
    def test_missing_optional_parser_fails_before_creating_a_run(self):
        with test_directory() as repo:
            revision = fixture(repo, {'Api.cs': 'class C {}\n'})
            script = Path(__file__).resolve().parents[1] / 'scripts/project_mapper.py'
            env = dict(os.environ)
            env.pop('PYTHONPATH', None)
            result = subprocess.run([sys.executable, '-S', str(script), str(repo), 'map', '--commit', revision, '--csharp'],
                                    text=True, capture_output=True, env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('C# extraction requires', result.stderr)
            self.assertFalse((repo / '.project-mapper').exists())



if __name__ == '__main__':
    unittest.main()
