import unittest

from test_acceptance import fixture, invoke, test_directory
from test_investigation import accept, add_question, load, publish_investigation, save, write_answer


class InvestigationClaims(unittest.TestCase):
    def test_scoped_absence_and_membership_leave_unanswered_question_open(self):
        with test_directory() as repo:
            rev = fixture(repo, {'service.toml': 'members = ["worker"]\nsubscribers = []\n'})
            run = invoke(repo, 'investigate', '--commit', rev)
            for key, text in [('members', 'Which components belong to this service?'),
                              ('subscribers', 'Which subscribers are configured in service.toml?'),
                              ('hosted', 'Which consumers are deployed in the hosted environment?')]:
                add_question(run, key, text, ['service.toml'])

            page = invoke(repo, 'read-input', run['run'], 'members', 'service.toml')
            locator = dict(path='service.toml', content_id=page['content_id'], start=1, end=1)
            claim = dict(source='component:worker', relation='member-of', target='service:payments',
                         condition='', evidence=[locator])
            write_answer(run, 'members', [claim])
            accept(repo, run, 'members')
            negative = write_answer(run, 'subscribers', [])
            absence = dict(statement='The subscriber list configured in service.toml is empty.',
                           evidence=[dict(locator, start=2, end=2)])
            save(negative, dict(load(negative), absence=absence))
            accept(repo, run, 'subscribers')

            publish_investigation(repo, run)
            result = invoke(repo, 'coverage')
            rows = {entry['area']: entry for entry in result['coverage']}
            self.assertEqual(result['status'], 'partial')
            self.assertTrue(rows['subscribers']['scoped_absence'])
            self.assertEqual(rows['subscribers']['reason'], absence['statement'])
            self.assertEqual(rows['subscribers']['paths'], ['service.toml'])
            self.assertFalse(rows['members']['scoped_absence'])
            self.assertEqual(rows['hosted']['status'], 'unexamined')
            self.assertFalse(rows['hosted']['scoped_absence'])
            negatives = [item for item in result['discrepancies'] if item['kind'] == 'scoped-absence']
            self.assertEqual(len(negatives), 1)
            self.assertEqual(negatives[0]['evidence'][0]['span'][:3], [2, 0, 2])
            members = invoke(repo, 'dimensions')['memberships']
            self.assertEqual([(row['dimension'], row['group_key'], row['node']) for row in members],
                             [('service', 'service:payments', 'component:worker')])
            self.assertEqual(members[0]['evidence'][0]['path'], 'service.toml')
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

    def test_negative_answer_requires_reviewable_text_evidence(self):
        with test_directory() as repo:
            rev = fixture(repo, {'config.json': '{"subscribers":[]}\n', 'binary.dat': 'a\0b'})
            run = invoke(repo, 'investigate', '--commit', rev)
            add_question(run, 'subscribers', 'Which subscribers are configured?', ['config.json'])
            source_id = next(entry['content_id'] for entry in load(run['inventory'])['entries']
                             if entry['path'] == 'binary.dat')
            locator = dict(path='binary.dat', content_id=source_id, start=1, end=1)
            shard = write_answer(run, 'subscribers', [])
            raw = load(shard)
            for status, gap, evidence, expected in [('answered', '', [], 'locator'),
                                                    ('answered', '', [locator], 'binary'),
                                                    ('partial', 'identity unknown', [locator], 'answered')]:
                with self.subTest(status=status, expected=expected):
                    save(shard, dict(raw, status=status, gap=gap,
                                     absence=dict(statement='The configured list is empty.', evidence=evidence)))
                    result = invoke(repo, 'check-shard', run['run'], 'subscribers', ok=False)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected, result.stderr)


if __name__ == '__main__':
    unittest.main()
