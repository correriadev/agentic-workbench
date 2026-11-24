"""Evidence, incremental publication and navigation for graph-led investigations."""

from pathlib import Path
import unittest

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, load, publish_investigation, save, write_answer


class InvestigationNavigation(unittest.TestCase):
    def setUp(self):
        self.repo = self.enterContext(test_directory())
        self.revision = fixture(self.repo, {
            'package.json': '{"bin":{"demo":"./cli/main.js"}}\n',
            'cli/main.js': 'import { run } from "../service/run.js";\nrun();\n',
            'service/run.js': 'import save from "../store/save.js";\nexport function run() { save(); }\n',
            'store/save.js': 'import send from "external";\nexport default function save() { send(); }\n',
            'tests/save.test.js': 'import save from "../store/save.js";\ntest("sends", () => save());\n',
            'tools/read.js': 'import save from "../store/save.js";\nexport const read = save;\n',
            'docs/manual.md': 'The demo stores results locally.\n',
        })
        invoke(self.repo, 'map', '--commit', self.revision)
        self.run = invoke(self.repo, 'investigate', '--commit', self.revision, '--from-graph')
        self.plan = load(self.run['plan'])
        self.refs = {row['path']: dict(path=row['path'], content_id=row['content_id'], start=1, end=1)
                     for row in load(self.run['inventory'])['entries']}

    def discovery(self, key, content, path):
        return dict(id=key, title=key, summary='Source-backed observation.', terms=[], content=content,
                    support=[dict(pointer='', evidence=[self.refs[path]])])

    def claim(self, source, relation, target, *paths, condition=''):
        return dict(source=source, relation=relation, target=target, condition=condition,
                    evidence=[self.refs[path] for path in paths])

    def shard(self, key, discoveries=(), claims=(), gap=''):
        path = write_answer(self.run, key, list(claims))
        save(path, dict(load(path), discoveries=list(discoveries), status='partial' if gap else 'answered', gap=gap))
        return accept(self.repo, self.run, key)

    def node(self, key):
        return invoke(self.repo, 'node', key)['nodes'][0]

    def test_disconnected_context_can_be_published_and_reconciled_across_shards(self):
        subject = 'file:cli/main.js'
        add_question(self.run, 'role', 'What starts the demo?', ['cli/main.js'])
        add_question(self.run, 'link', 'Where is the role attached?', ['package.json'])
        checked = self.shard('role', [self.discovery('cli-role', dict(subject_node=subject, role='Demo entry.'),
                                                   'cli/main.js'),
                                      self.discovery('shared', dict(role='Shared context.'), 'cli/main.js')])
        self.assertEqual([d['discovery'] for d in checked['context_diagnostics']], ['cli-role'])
        publish_investigation(self.repo, self.run)
        node = self.node(subject)
        self.assertEqual(node['semantic_context']['status'], 'not-linked')
        diagnostic, = node['context_diagnostics']
        self.assertEqual((diagnostic['discovery'], diagnostic['subject_node']), ('cli-role', subject))
        self.assertEqual(diagnostic['status'], 'missing-subject-link')
        self.assertTrue(diagnostic['evidence'])
        self.assertEqual(invoke(self.repo, 'verify')['integrity'], 'ok')
        self.shard('link', claims=[self.claim(subject, 'explained-by', 'cli-role', 'cli/main.js', 'package.json')])
        publish_investigation(self.repo, self.run)
        node = self.node(subject)
        self.assertFalse(node['context_diagnostics'])
        self.assertEqual(node['semantic_context']['node_role_status'], 'reviewed')
        self.assertFalse(invoke(self.repo, 'coverage')['context_diagnostics'])

    def test_context_claim_waits_for_unaccepted_discovery(self):
        subject = 'file:cli/main.js'
        add_question(self.run, 'link', 'Which discovery explains the entry?', ['cli/main.js'])
        add_question(self.run, 'role', 'What starts the demo?', ['cli/main.js'])
        self.shard('link', claims=[self.claim('cli-role', 'describes', subject, 'cli/main.js')])
        publication = publish_investigation(self.repo, self.run)
        self.assertEqual(publication['deferred_claims'][0]['missing_endpoints'], ['cli-role'])
        self.assertFalse(self.node(subject)['semantic_context']['entries'])
        self.assertEqual(invoke(self.repo, 'verify')['integrity'], 'ok')
        self.shard('role', [self.discovery('cli-role', dict(subject_node=subject, role='Demo entry.'), 'cli/main.js')])
        publication = publish_investigation(self.repo, self.run)
        self.assertFalse(publication.get('deferred_claims'))
        self.assertEqual(self.node(subject)['semantic_context']['node_role_status'], 'reviewed')

    def test_scoped_flow_follows_source_leads_and_partial_remains_partial(self):
        anchor = 'command:package.json:demo'
        flow = next(q for q in self.plan['questions'] if q.get('scope') == {'kind': 'flow', 'anchor': anchor})
        self.assertTrue({'package.json', 'cli/main.js', 'service/run.js', 'store/save.js', 'tests/save.test.js'}
                        <= set(flow['seeds']))
        self.assertTrue(any(q.get('scope') == {'kind': 'flow', 'anchor': 'file:tools/read.js'}
                            for q in self.plan['questions']))
        files = [q for q in self.plan['questions'] if q.get('scope') == {'kind': 'file'}]
        self.assertTrue(any('docs/manual.md' in q['seeds'] for q in files))
        self.assertIn(anchor, flow['question'])
        unit = invoke(self.repo, 'graph-unit', self.run['run'], flow['id'], '--summary')
        self.assertEqual(unit['question']['scope'], flow['scope'])
        static = invoke(self.repo, 'trace', 'file:cli/main.js', '--direction', 'out', '--type', 'calls')
        self.assertEqual(static['edges'], [])
        gap = 'The external send destination is selected outside the snapshot.'
        self.shard(flow['id'], [self.discovery('demo-flow', {'flow': 'The demo calls the service.', 'gaps': [gap]},
                                             'cli/main.js')],
                   [self.claim('demo-flow', 'describes', 'file:cli/main.js', 'cli/main.js'),
                    self.claim('file:cli/main.js', 'calls', 'file:service/run.js', 'cli/main.js', 'service/run.js',
                               condition='When the CLI module runs')], gap=gap)
        publish_investigation(self.repo, self.run)
        node = self.node('file:cli/main.js')
        self.assertEqual(node['flow_discoveries'][0]['discovery'], 'demo-flow')
        self.assertTrue(any(item['reason'] == gap for item in node['investigation_gaps']))
        trace = invoke(self.repo, 'trace', 'file:cli/main.js', '--direction', 'out', '--type', 'calls')
        self.assertEqual(trace['edges'][0]['conditions'], ['When the CLI module runs'])
        counts = invoke(self.repo, 'coverage', '--summary')
        self.assertIn('file_citation', counts)
        self.assertIn('semantic_context', counts)
        self.assertEqual(counts['flow_investigation']['statuses']['partial'], 1)
        self.assertTrue(any(row['status'] == 'unexamined' for row in invoke(self.repo, 'coverage')['coverage']))
        self.assertEqual(invoke(self.repo, 'verify')['integrity'], 'ok')

    def test_reviewed_discrepancy_connects_both_supported_accounts(self):
        add_question(self.run, 'accounts', 'Do the manual and code agree on demo storage?', ['docs/manual.md'])
        reports = [self.discovery('manual', {'behavior': 'Stores locally.'}, 'docs/manual.md'),
                   self.discovery('implementation', {'behavior': 'Delegates to send.'}, 'store/save.js'),
                   self.discovery('other', {'behavior': 'Calls send.'}, 'store/save.js')]
        self.shard('accounts', reports, [self.claim('manual', 'conflicts-with', 'implementation',
                                                   'docs/manual.md', 'store/save.js', condition='Default demo invocation')])
        publish_investigation(self.repo, self.run)
        edge, = self.node('implementation')['reviewed_discrepancies']
        self.assertEqual((edge['source'], edge['target']), ('manual', 'implementation'))
        self.assertEqual(edge['conditions'], ['Default demo invocation'])
        self.assertEqual({ref['path'] for ref in edge['evidence']}, {'docs/manual.md', 'store/save.js'})
        self.assertEqual(invoke(self.repo, 'open', edge['source'])['support'][0]['evidence'][0]['path'],
                         'docs/manual.md')
        self.assertFalse(self.node('other')['reviewed_discrepancies'])
        self.assertEqual(invoke(self.repo, 'verify')['integrity'], 'ok')
