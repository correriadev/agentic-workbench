import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from test_acceptance import fixture, git, invoke, test_directory
from test_investigation import accept, add_question, publish_investigation, save


def citation(repo, run, path):
    source = invoke(repo, 'read-input', run['run'], 'contract', path, '--count', '1')
    return dict(path=path, content_id=source['content_id'], start=1, end=1)


class DiscoveryCLI(unittest.TestCase):
    def test_a_contract_lookup_tracks_the_mapping_at_each_revision(self):
        with test_directory() as repo:
            contract = {'buyer': {'type': 'string', 'format': 'uuid', 'required': True}}
            mapping = 'def persist(payload, row): row["buyer_id"] = payload["buyer"]\n'
            first = fixture(repo, {'contract.json': json.dumps(contract) + '\n', 'store.py': mapping})
            (repo / 'store.py').write_text(mapping.replace('buyer_id', 'party_id'), encoding='utf-8')
            git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test',
                'commit', '-qam', 'change destination')
            second = git(repo, 'rev-parse', 'HEAD').decode().strip()

            for revision, destination in [(first, 'buyer_id'), (second, 'party_id'), (first, 'buyer_id')]:
                with self.subTest(revision=revision):
                    run = invoke(repo, 'investigate', '--commit', revision)
                    add_question(run, 'contract', 'Where is the buyer reference stored?', ['contract.json'])
                    spec_ref = citation(repo, run, 'contract.json')
                    storage_ref = citation(repo, run, 'store.py')
                    content = {**contract, 'persisted_as': destination}
                    support = [dict(pointer='/buyer', evidence=[spec_ref]),
                               dict(pointer='/persisted_as', evidence=[storage_ref])]
                    node = dict(id='d17', title='Buyer reference', summary='Wire requirements and storage destination',
                                terms=['client identifier'], content=content, support=support)
                    edge = dict(source='d17', relation='stored-in', target='column:' + destination,
                                condition='', evidence=[storage_ref])
                    shard = dict(snapshot=run['snapshot']['identity'], question='contract', status='answered',
                                 gap='', discoveries=[node], claims=[edge])
                    save(Path(run['shards']) / 'contract.json', shard)
                    accept(repo, run, 'contract')
                    self.assertEqual(publish_investigation(repo, run)['discoveries'], 1)
                    self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')
                    hits = invoke(repo, 'search', 'client identifier', '--limit', '1')
                    self.assertEqual(hits['snapshot']['revision'], revision)
                    self.assertEqual(hits['matches'][0]['key'], 'd17')
                    self.assertNotIn('content', hits['matches'][0])
                    found = invoke(repo, 'open', hits['matches'][0]['key'])
                    self.assertEqual((found['snapshot']['revision'], found['content']), (revision, content))
                    cli = Path(__file__).resolve().parents[1] / 'scripts/project_mapper.py'
                    offline = subprocess.run([sys.executable, str(cli), str(repo), '--offline', 'open', 'd17'],
                                             capture_output=True, text=True, env=dict(os.environ, PATH=''))
                    self.assertEqual(offline.returncode, 0, offline.stderr)
                    self.assertEqual(json.loads(offline.stdout)['content'], content)
                    refs = {s['pointer']: s['evidence'][0] for s in found['support']}
                    self.assertEqual(refs['/persisted_as']['content_id'], storage_ref['content_id'])
                    self.assertEqual(refs['/buyer']['path'], 'contract.json')
                    edges = invoke(repo, 'trace', found['key'], '--depth', '1')['edges']
                    self.assertEqual([edge['target'] for edge in edges], ['column:' + destination])
