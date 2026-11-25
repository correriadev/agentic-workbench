from contextlib import closing
from pathlib import Path
import shutil
import sqlite3
import unittest

from test_acceptance import fixture, git, invoke, rows, test_directory
from test_investigation import accept, load, publish_investigation, save, write_answer


def commit(repo):
    git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test',
        '-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-qm', 'refresh fixture')
    return git(repo, 'rev-parse', 'HEAD').decode().strip()


class Refresh(unittest.TestCase):
    def test_cached_extraction_rebinds_imports_and_drops_old_paths(self):
        repo = self.enterContext(test_directory())
        base = fixture(repo, {'main.js': 'import "./dep.js";\n', 'dep.js': 'export const value = 1;\n',
                              'worker.py': 'def worker():\n    return 1\n'})
        invoke(repo, 'map', '--commit', base)
        output = repo / '.project-mapper'
        self.assertEqual({path.name for path in output.iterdir()},
                         {'graph.sqlite', 'cache.sqlite', 'README.md', 'publication.sqlite'})
        git(repo, 'mv', 'dep.js', 'dep.ts')
        head = commit(repo)
        (repo / 'main.js').write_text('import "./dirty.js";\n', encoding='utf-8')

        result = invoke(repo, 'refresh', '--commit', 'HEAD')
        self.assertEqual(result['snapshot']['revision'], head)
        self.assertEqual((result['mode'], result['base_revision'], result['changed_paths']),
                         ('incremental', base, 2))
        self.assertEqual((result['reused_files'], result['extracted_files']), (2, 1))
        self.assertEqual(rows(repo, "SELECT target FROM relationships "
                                    "WHERE source='file:main.js' AND type='imports'"),
                         [('file:dep.ts',)])
        self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')
        with closing(sqlite3.connect(output / 'cache.sqlite')) as cache:
            self.assertEqual({row[0] for row in cache.execute('SELECT path FROM extracts')},
                             {'dep.ts', 'main.js', 'worker.py'})
        graph = output / 'graph.sqlite'
        stamp = graph.stat().st_mtime_ns
        unchanged = invoke(repo, 'refresh', '--commit', head)
        self.assertEqual(unchanged['mode'], 'unchanged')
        self.assertEqual(graph.stat().st_mtime_ns, stamp)
        self.assertFalse(any(output.glob('staging-*')))

    def test_full_extraction_without_a_compatible_cache_or_ancestry(self):
        repo = self.enterContext(test_directory())
        base = fixture(repo, {'main.py': 'def run():\n    return 1\n'})
        self.assertEqual(invoke(repo, 'refresh', '--commit', base)['mode'], 'full')
        (repo / '.project-mapper/cache.sqlite').unlink()
        (repo / 'other.py').write_text('x = 1\n', encoding='utf-8')
        git(repo, 'add', 'other.py')
        first = commit(repo)
        uncached = invoke(repo, 'refresh', '--commit', first)
        self.assertEqual((uncached['mode'], uncached['changed_paths'], uncached['reused_files']), ('full', 1, 0))

        git(repo, 'checkout', '--detach', base)
        (repo / 'another.py').write_text('x = 2\n', encoding='utf-8')
        git(repo, 'add', 'another.py')
        second = commit(repo)
        divergent = invoke(repo, 'refresh', '--commit', second)
        self.assertEqual(divergent['mode'], 'full')
        self.assertEqual(divergent['base_revision'], first)
        self.assertIsNone(divergent['changed_paths'])
        self.assertEqual(divergent['reused_files'], 0)
        self.assertEqual(invoke(repo, 'verify')['snapshot']['revision'], second)

    def test_reuses_review_only_when_inputs_match_and_resumes_on_change(self):
        repo = self.enterContext(test_directory())
        base = fixture(repo, {'package.json': '{"name":"demo","main":"app.js"}\n', 'app.js': 'run();\n'})
        invoke(repo, 'map', '--commit', base)
        run = invoke(repo, 'investigate', '--commit', base, '--from-graph')
        plan = load(run['plan'])
        plan['questions'] = [dict(id='startup', question='Where is the entry point declared?',
                                  seeds=['package.json'], depends_on=[], node_ids=['file:package.json'],
                                  scope={'kind': 'file'})]
        save(run['plan'], plan)
        page = invoke(repo, 'read-input', run['run'], 'startup', 'package.json', '--count', '1')
        write_answer(run, 'startup', [dict(source='file:package.json', relation='describes',
                                          target='file:app.js', condition='',
                                          evidence=[dict(path='package.json', content_id=page['content_id'],
                                                         start=1, end=1)])])
        accept(repo, run, 'startup')
        publish_investigation(repo, run)

        same_input = invoke(repo, 'refresh', '--commit', commit(repo))
        self.assertEqual((same_input['reused_questions'], same_input['pending_questions']), (1, 0))
        reviewed = invoke(repo, 'check-plan', same_input['run'], '--question', 'startup')
        self.assertEqual(reviewed['progress'], 'accepted-answered')
        self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')
        self.assertEqual(len(rows(repo, "SELECT id FROM relationships WHERE type='describes'")), 1)

        git(repo, 'rm', 'package.json')
        changed = invoke(repo, 'refresh', '--commit', commit(repo))
        self.assertEqual((changed['reused_questions'], changed['pending_questions']), (0, 1))
        pending = invoke(repo, 'check-plan', changed['run'], '--question', 'startup')
        self.assertEqual(pending['progress'], 'unexamined')
        self.assertEqual(pending['question']['seeds'], [])
        self.assertNotIn('node_ids', pending['question'])
        prior = load(repo / '.project-mapper' / changed['run'] / 'prior-review.json')['startup']
        self.assertEqual(prior['snapshot'], same_input['snapshot'])
        self.assertEqual(prior['shard']['status'], 'answered')
        self.assertEqual(rows(repo, "SELECT id FROM relationships WHERE type='describes'"), [])
        self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')
        publish_investigation(repo, changed)

    def test_cleanup_previews_known_artifacts_and_preserves_saved_runs(self):
        repo = self.enterContext(test_directory())
        base = fixture(repo, {'app.py': 'def app():\n    return 1\n'})
        invoke(repo, 'build', '--commit', base)
        output = repo / '.project-mapper'
        self.assertEqual({path.name for path in output.iterdir()},
                         {'graph.sqlite', 'README.md', 'publication.sqlite'})
        run = invoke(repo, 'prepare', '--commit', base)
        stage = Path(run['plan']).parent
        old_attempt = stage / ('publish-' + 'a' * 32)
        old_attempt.mkdir()
        failed_attempt = stage / ('publish-' + 'd' * 32)
        failed_attempt.mkdir()
        shutil.copyfile(output / 'graph.sqlite', failed_attempt / 'candidate.sqlite')
        shutil.copyfile(output / 'README.md', failed_attempt / 'README.md')
        uncertain = stage / ('publish-' + 'e' * 32)
        uncertain.mkdir()
        (uncertain / 'README.md').write_text('My notes\n', encoding='utf-8')
        own = output / ('staging-' + 'b' * 32)
        own.mkdir()
        save(own / 'owner.json', {'publication_workspace': own.name})
        (own / 'candidate.sqlite').touch()
        foreign = output / ('staging-' + 'c' * 32)
        foreign.mkdir()
        save(foreign / 'owner.json', {'publication_workspace': foreign.name})
        (foreign / 'notes.txt').write_text('Keep this file.\n', encoding='utf-8')
        export = output / 'map.json'
        export.write_text('{}\n', encoding='utf-8')

        expected = {own.name, old_attempt.relative_to(output).as_posix(), failed_attempt.relative_to(output).as_posix()}
        preview = invoke(repo, 'cleanup')
        self.assertEqual(set(preview['paths']), expected)
        self.assertEqual(preview['removed'], [])
        self.assertTrue(own.exists() and old_attempt.exists() and failed_attempt.exists())
        self.assertEqual(set(invoke(repo, 'cleanup', '--apply')['removed']), expected)
        self.assertFalse(own.exists() or old_attempt.exists() or failed_attempt.exists())
        self.assertTrue(stage.exists() and foreign.exists() and export.exists() and uncertain.exists())
        self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')
