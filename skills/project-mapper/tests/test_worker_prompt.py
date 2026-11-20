import json
from pathlib import Path
import unittest

from test_acceptance import SCRIPTS, fixture, invoke, test_directory
from test_investigation import add_question, load


class WorkerPrompt(unittest.TestCase):
    def test_dispatch_is_pointer_only_and_repair_appends_to_same_assignment(self):
        with test_directory() as workspace:
            repo = workspace / 'repository with spaces'
            repo.mkdir()
            seed = 'entry points.toml'
            rev = fixture(repo, {seed: 'implementation = "DO_NOT_COPY_SOURCE_INTO_DISPATCH"\n'})
            run = invoke(repo, 'investigate', '--commit', rev)
            add_question(run, 'invoke', 'Which command invokes the application?', [seed])
            add_question(run, 'receive', 'Which receiver consumes the resulting notification?', [seed])
            plan = load(run['plan'])
            decisions = Path(run['decisions'])
            original = decisions.read_bytes()
            for question in plan['questions']:
                key = question['id']
                with self.subTest(question=key):
                    rendered = invoke(repo, 'worker-prompt', run['run'], key)['prompt']
                    prefix = (SCRIPTS.parent / 'references/worker.md').read_text(encoding='utf-8').rstrip()
                    assignment = {
                        'root': str(repo),
                        'mapper': str(SCRIPTS / 'project_mapper.py'),
                        'run': run['run'],
                        'snapshot': plan['snapshot'],
                        'output_language': 'en',
                        'plan': run['plan'],
                        'inventory': run['inventory'],
                        'question': question,
                        'shard': str(Path(run['shards']) / f'{key}.json'),
                    }
                    serialized = json.dumps(assignment, sort_keys=True, separators=(',', ':'))
                    self.assertEqual(rendered, prefix + '\n\nAssignment\n' + serialized)
                    diagnostic = 'Recheck the locator for "implementation".'
                    retry = invoke(repo, 'worker-prompt', run['run'], key, '--repair', diagnostic)['prompt']
                    suffix = json.dumps({'diagnostic': diagnostic}, separators=(',', ':'))
                    self.assertEqual(retry, rendered + '\n\nRepair\n' + suffix)
            missing = invoke(repo, 'worker-prompt', run['run'], 'missing', ok=False)
            self.assertNotEqual(missing.returncode, 0)
            self.assertEqual(decisions.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
