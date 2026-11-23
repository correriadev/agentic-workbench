import json
import os
from contextlib import closing, contextmanager
from pathlib import Path
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4


SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
PUBLIC_URL = 'https://github.com/pallets/click.git'
PUBLIC_REV = '934813e4d421071a1b3db3973c02fe2721359a6e'
TEST_TEMP = os.environ.get('PROJECT_MAPPER_TEST_TEMP')


@contextmanager
def test_directory():
    parent = Path(TEST_TEMP or tempfile.gettempdir()).resolve()
    path = parent / f'project-mapper-test-{uuid4().hex}'
    path.mkdir()
    try:
        yield path
    finally:
        if path.resolve() == path and path.parent == parent:
            def remove_readonly(operation, name, error):
                if os.name != 'nt' or not isinstance(error, PermissionError):
                    raise error
                os.chmod(name, stat.S_IWRITE)
                operation(name)

            shutil.rmtree(path, onexc=remove_readonly)

# Oracles derived from the fixture source, before running the mapper.
FLAT = {
    '.gitignore': 'cache/\nkept/*.py\nflat/other.py\n',
    'flat/__init__.py': '',
    'flat/main.py': 'from .worker import run as handle\n\ndef go():\n    return handle()\n'
                    '\ndef shadow(handle):\n    return handle()\n',
    'flat/worker.py': 'def run():\n    return 1\n',
    'flat/other.py': 'def run():\n    return 2\n',
    'flat/extra.py': 'import flat.worker as w\n\ndef outside(flag):\n    if flag:\n        return w.run()\n',
    'maintenance.py': 'from flat.worker import run\n\ndef maintain():\n    return run()\n',
    'kept/.gitignore': '!save.py\n',
    'deleted.py': 'def old():\n    pass\n',
    'staged-delete.py': '',
    'sentinel.py': 'from pathlib import Path\nPath("executed").touch()\n',
}
SRC = {
    'pyproject.toml': '[project]\nname = "wheelhouse"\n[project.scripts]\nwheel = "wheelhouse.cli:main"\n'
                      '[tool.setuptools.package-dir]\n"" = "lib"\n',
    'lib/wheelhouse/__init__.py': '',
    'lib/wheelhouse/cli.py': 'from .impl import work\n\ndef main():\n    return work()\n',
    'lib/wheelhouse/impl.py': 'def work():\n    return 1\n',
    'lib/wheelhouse/check.py': 'from .impl import work\n\ndef verify():\n    return work()\n',
    'lib/wheelhouse/twin.py': 'def work():\n    return 1\n',
    'tests/test_invalid.py': 'def unreadable(\n',
    'asyncapi.yaml': 'asyncapi: 3.0.0\n',
    'architecture.md': '# Architecture\n\nRuntime is declared separately.\n',
}
FLAT_CALL = ('function:flat.main:go', 'function:flat.worker:run')
EXTRA_CALL = ('function:flat.extra:outside', 'function:flat.worker:run')
MAINTENANCE_CALL = ('function:maintenance:maintain', 'function:flat.worker:run')
SRC_CALL = ('function:wheelhouse.cli:main', 'function:wheelhouse.impl:work')
CHECK_CALL = ('function:wheelhouse.check:verify', 'function:wheelhouse.impl:work')
PUBLIC_CALL = ('function:click.termui:secho', 'function:click.utils:echo')


def git(repo, *args):
    env = dict(os.environ, GIT_AUTHOR_DATE='2026-01-01T00:00:00Z', GIT_COMMITTER_DATE='2026-01-01T00:00:00Z',
               GIT_OPTIONAL_LOCKS='0')
    return subprocess.check_output(['git', '-c', f'core.hooksPath={os.devnull}', '-c', 'core.autocrlf=false',
                                    '-C', str(repo), *args], env=env)


def invoke(repo, *args, script='project_mapper.py', ok=True):
    result = subprocess.run([sys.executable, '-B', str(SCRIPTS / script), str(repo), *args],
                            text=True, encoding='utf-8', capture_output=True)
    if ok:
        assert result.returncode == 0, result.stderr or result.stdout
        return json.loads(result.stdout)
    return result


def fixture(repo, files):
    git(repo, 'init', '-q', '--object-format=sha1', '--initial-branch=main')
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode())
    git(repo, 'add', '-f', '.')
    git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test',
        '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')
    return git(repo, 'rev-parse', 'HEAD').decode().strip()


def rows(repo, sql, args=()):
    path = repo / '.project-mapper' / 'graph.sqlite'
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
        return db.execute(sql, args).fetchall()


def calls(repo):
    return set(rows(repo, "SELECT source,target FROM relationships WHERE type='calls' AND state='resolved'"))


class Mapping(unittest.TestCase):
    def assert_inventory(self, repo, rev):
        expected = set(git(repo, 'ls-tree', '--full-tree', '-r', '--name-only', '-z', rev)
                       .decode().strip('\0').split('\0'))
        self.assertEqual(expected, {path for path, in rows(repo, 'SELECT path FROM inventory')})

    def test_flat_pinned_and_worktree(self):
        with test_directory() as repo:
            rev = fixture(repo, FLAT)
            (repo / 'flat/worker.py').write_text('def changed():\n    pass\n')
            (repo / 'deleted.py').unlink()
            git(repo, 'rm', '--', 'staged-delete.py')
            (repo / 'kept/save.py').write_text('def kept():\n    pass\n')
            (repo / 'kept/skip.py').write_text('def ignored():\n    pass\n')
            (repo / '.git/info/exclude').write_text('info-only.py\n')
            (repo / '.git/info/mapper-test-global-ignore').write_text('global-only.py\n')
            git(repo, 'config', 'core.excludesFile', '.git/info/mapper-test-global-ignore')
            (repo / 'info-only.py').write_text('def ignored():\n    pass\n')
            (repo / 'global-only.py').write_text('def ignored():\n    pass\n')
            (repo / 'cache').mkdir()
            (repo / 'cache/generated.py').write_text('def artifact():\n    pass\n')
            before = git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
            index = (repo / '.git/index').read_bytes()
            scan = invoke(repo, '--commit', rev, script='scan_files.py')
            self.assertEqual(scan['snapshot']['revision'], rev)
            invoke(repo, 'build', '--commit', rev)
            self.assert_inventory(repo, rev)
            self.assertEqual(calls(repo), {FLAT_CALL, EXTRA_CALL, MAINTENANCE_CALL})
            forward = invoke(repo, 'trace', FLAT_CALL[0], '--type', 'calls', '--direction', 'out')
            back = invoke(repo, 'trace', FLAT_CALL[1], '--type', 'calls', '--direction', 'in')
            self.assertIn(FLAT_CALL[1], forward['nodes'])
            self.assertIn(FLAT_CALL[0], back['nodes'])
            self.assertIn(MAINTENANCE_CALL[0], back['nodes'])
            anchors = {o['path'] for o in forward['edges'][0]['evidence']}
            self.assertEqual(anchors, {'flat/main.py', 'flat/worker.py'})
            self.assertEqual(invoke(repo, 'verify')['snapshot']['revision'], rev)
            after = git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all', '--', '.',
                        ':(exclude).project-mapper')
            self.assertEqual(before, after)
            self.assertEqual(index, (repo / '.git/index').read_bytes())
            self.assertEqual(rev, git(repo, 'rev-parse', 'HEAD').decode().strip())
            self.assertFalse((repo / 'executed').exists())
            shadow = invoke(repo, 'node', 'function:flat.main:shadow')['nodes'][0]
            self.assertTrue(any(edge['state'] == 'unresolved' and FLAT_CALL[1] in edge['candidates']
                                for edge in shadow['outgoing']))
            with closing(sqlite3.connect(repo / '.project-mapper/graph.sqlite')) as db, db:
                db.execute('UPDATE relationships SET target=? WHERE source=? AND target=?',
                           ('function:flat.other:run', *FLAT_CALL))
            self.assertIn('do not reproduce', invoke(repo, 'verify', ok=False).stderr)
            invoke(repo, 'build', '--worktree')
            records = dict(rows(repo, 'SELECT path,status FROM inventory'))
            self.assertEqual(records['deleted.py'], 'deleted')
            self.assertEqual(records['staged-delete.py'], 'deleted')
            self.assertEqual(records['flat/other.py'], 'analyzed')
            self.assertEqual(records['kept/save.py'], 'analyzed')
            self.assertEqual(records['kept/skip.py'], 'excluded')
            self.assertEqual(records['info-only.py'], 'excluded')
            self.assertEqual(records['global-only.py'], 'excluded')
            self.assertEqual(records['cache/'], 'excluded')
            self.assertFalse(calls(repo))
            self.assertFalse(any(path.startswith('.project-mapper/') for path in records))

    def test_declared_layout_falsification_and_publication(self):
        with test_directory() as repo:
            rev = fixture(repo, SRC)
            original = invoke(repo, 'build', '--commit', rev)['snapshot']
            self.assert_inventory(repo, rev)
            self.assertEqual(calls(repo), {SRC_CALL, CHECK_CALL})
            dimensions = invoke(repo, 'dimensions')['memberships']
            membership = {m['dimension'] for m in dimensions if m['node'] == SRC_CALL[0]}
            self.assertEqual(membership, {'source-package', 'declared-entry-point'})
            duplicate = rows(repo, "SELECT DISTINCT path,content_id FROM occurrences "
                                   "WHERE path LIKE '%/impl.py' OR path LIKE '%/twin.py'")
            self.assertEqual(len(duplicate), 2)
            self.assertEqual(len({digest for _, digest in duplicate}), 1)
            coverage = invoke(repo, 'coverage')
            self.assertTrue(any(row['status'] == 'unsupported' and row['family'] == 'event-contract'
                                for row in coverage['coverage']))
            self.assertTrue(any(row['status'] == 'partial' and row['family'] == 'semantic'
                                for row in coverage['coverage']))
            self.assertTrue(any(row['status'] == 'analyzed' and row['scoped_absence']
                                for row in coverage['coverage']))
            limited = invoke(repo, 'trace', SRC_CALL[0], '--type', 'calls', '--depth', '0')
            self.assertTrue(limited['truncated'])
            self.assertEqual(coverage, invoke(repo, 'coverage'))
            up = invoke(repo, 'trace', SRC_CALL[0], '--type', 'contains', '--direction', 'both')
            self.assertNotIn('module:wheelhouse.twin', up['nodes'])

            cli = repo / 'lib/wheelhouse/cli.py'
            cli.write_text(SRC['lib/wheelhouse/cli.py'].replace('return work()', 'return None'))
            prepared = invoke(repo, 'prepare', '--worktree')
            self.assertEqual(invoke(repo, 'verify')['snapshot'], original)
            invoke(repo, 'publish', prepared['run'])
            with self.assertRaises(AssertionError):
                self.assertIn(SRC_CALL, calls(repo))
            self.assertEqual(len(rows(repo, 'SELECT key FROM nodes WHERE key IN (?,?)', SRC_CALL)), 2)
            cli.write_text(SRC['lib/wheelhouse/cli.py'])
            invoke(repo, 'build', '--worktree')
            self.assertIn(SRC_CALL, calls(repo))

            manifest = repo / 'pyproject.toml'
            manifest.write_text(SRC['pyproject.toml'].replace('= "lib"', '= "missing"'))
            invoke(repo, 'build', '--worktree')
            self.assertFalse(calls(repo))
            self.assertTrue(any(row['status'] == 'partial' and 'root' in row['reason']
                                for row in invoke(repo, 'coverage')['coverage']))
            prepared = invoke(repo, 'prepare', '--worktree')
            prior = invoke(repo, 'verify')['snapshot']
            cli.write_text('different bytes\n')
            failed = invoke(repo, 'publish', prepared['run'], ok=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('snapshot', failed.stderr)
            self.assertEqual(invoke(repo, 'coverage')['snapshot'], prior)

    def test_symlinked_output(self):
        with test_directory() as base:
            repo = base / 'repo'
            repo.mkdir()
            outside = base / 'outside'
            outside.mkdir()
            rev = fixture(repo, FLAT)
            try:
                (repo / '.project-mapper').symlink_to(outside, target_is_directory=True)
            except OSError:
                if os.name != 'nt':
                    raise
                subprocess.run(['cmd', '/c', 'mklink', '/J', str(repo / '.project-mapper'), str(outside)],
                               check=True, capture_output=True)
            result = invoke(repo, 'build', '--commit', rev, ok=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('output path', result.stderr)
            self.assertEqual(list(outside.iterdir()), [])

    def test_shard_admission_and_deterministic_replay(self):
        with test_directory() as repo:
            rev = fixture(repo, SRC)
            result = invoke(repo, 'build', '--commit', rev)
            prior = rows(repo, "SELECT key,value FROM metadata ORDER BY key")
            prior_edges = rows(repo, 'SELECT * FROM relationships ORDER BY id')
            invoke(repo, 'build', '--commit', rev)
            self.assertEqual(rows(repo, "SELECT key,value FROM metadata ORDER BY key"), prior)
            self.assertEqual(rows(repo, 'SELECT * FROM relationships ORDER BY id'), prior_edges)

            run = invoke(repo, 'prepare', '--commit', rev, '--agent-review')
            plan = json.loads(Path(run['plan']).read_text(encoding='utf-8'))
            root_task = next(item for item in run['review_tasks'] if plan['tasks'][item['id']]['area'] == '.')
            tests_task = next(item for item in run['review_tasks'] if plan['tasks'][item['id']]['area'] == 'tests')
            input_path = 'architecture.md'
            found = invoke(repo, 'read-input', run['run'], root_task['id'], input_path, '--count', '1')
            self.assertEqual(found['lines'], ['# Architecture'])
            denied = invoke(repo, 'read-input', run['run'], tests_task['id'], input_path, ok=False)
            self.assertNotEqual(denied.returncode, 0)
            denied = invoke(repo, 'read-input', run['run'], root_task['id'], input_path,
                            '--also', plan['tasks'][tests_task['id']]['paths'][0], '1', '1', ok=False)
            self.assertIn('outside this worker assignment', denied.stderr)
            self.assertEqual(denied.stdout, '')
            good = dict(plan=plan['id'], task=root_task['id'], snapshot=plan['snapshot'],
                        status='partial', inputs=[input_path], findings=[
                            dict(path=input_path, content_id=found['content_id'], line=1,
                                 kind='architecture-declaration')])
            Path(root_task['path']).write_text(json.dumps(good), encoding='utf-8')
            Path(tests_task['path']).write_text(json.dumps(dict(good, task=tests_task['id'])), encoding='utf-8')
            self.assertEqual(invoke(repo, 'check-shard', run['run'], root_task['id'])['status'], 'partial')
            self.assertNotEqual(invoke(repo, 'check-shard', run['run'], tests_task['id'], ok=False).returncode, 0)
            rogue = Path(root_task['path']).with_name('unassigned.json')
            rogue.write_text('{}')
            self.assertIn('task ownership', invoke(repo, 'publish', run['run'], ok=False).stderr)
            self.assertEqual(invoke(repo, 'verify')['snapshot'], result['snapshot'])
            rogue.unlink()
            published = invoke(repo, 'publish', run['run'])
            self.assertIsNotNone(published['supplemental_fingerprint'])
            self.assertEqual(rows(repo, 'SELECT * FROM relationships ORDER BY id'), prior_edges)
            coverage = invoke(repo, 'coverage', '--family', 'agent-review')
            self.assertEqual({(row['area'], row['status']) for row in coverage['coverage']},
                             {('.', 'partial'), ('lib', 'unexamined'), ('tests', 'blocked')})
            self.assertTrue(any(item['kind'] == 'supplemental-signal' for item in coverage['discrepancies']))
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')

    def test_public_click(self):
        checkout = os.environ.get('PROJECT_MAPPER_CLICK')
        if not checkout:
            self.skipTest(f'BLOCKED: set PROJECT_MAPPER_CLICK to a checkout of {PUBLIC_URL} at {PUBLIC_REV}')
        repo = Path(checkout).resolve()
        self.assertEqual(git(repo, 'rev-parse', 'HEAD').decode().strip(), PUBLIC_REV)
        invoke(repo, 'build', '--commit', PUBLIC_REV)
        self.assert_inventory(repo, PUBLIC_REV)
        self.assertIn(PUBLIC_CALL, calls(repo))
        self.assertIn(('module:click.termui', 'module:click.utils'), rows(
            repo, "SELECT source,target FROM relationships WHERE type='imports' AND state='resolved'"))
        self.assertIn(('source-package', 'click', 'module:click.termui'), rows(
            repo, 'SELECT dimension,group_key,node FROM memberships'))
        self.assertNotIn((PUBLIC_CALL[0], 'function:click.termui:echo'), calls(repo))
        self.assertTrue(any(row['status'] == 'partial' for row in invoke(repo, 'coverage')['coverage']))
        result = invoke(repo, 'trace', PUBLIC_CALL[1], '--direction', 'in', '--type', 'calls')
        self.assertIn(PUBLIC_CALL[0], result['nodes'])
        self.assertEqual(invoke(repo, 'verify')['snapshot']['revision'], PUBLIC_REV)


if __name__ == '__main__':
    unittest.main()
