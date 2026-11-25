"""Git snapshot inventory and byte reader shared by every mapping stage."""

import argparse
from contextlib import contextmanager
from functools import cache
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import threading


class MappingError(Exception):
    pass


def canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False)


def digest(data):
    return hashlib.sha256(canonical(data).encode()).hexdigest()


@cache
def git_executable(start):
    # Resolve a PATH executable independently of the target's current directory.
    name = 'git.exe' if os.name == 'nt' else 'git'
    for folder in os.get_exec_path():
        directory = Path(folder.strip('"'))
        if directory.is_absolute() and (found := shutil.which(str(directory / name))):
            executable = Path(found).resolve()
            if not executable.is_relative_to(start):
                return executable
    raise MappingError('Git executable unavailable outside target')


def git_command(root, *args):
    # Inherit the normal Git config and exclude files, but pin the repo and disable transports.
    config_vars = {'GIT_CONFIG_GLOBAL', 'GIT_CONFIG_SYSTEM', 'GIT_CONFIG_NOSYSTEM'}
    env = {key: value for key, value in os.environ.items()
           if not key.startswith('GIT_') or key in config_vars}
    env.update(GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1',
               GIT_ALLOW_PROTOCOL='', GIT_TERMINAL_PROMPT='0')
    return dict(args=[str(git_executable(root)), '-C', str(root), '-c', 'core.fsmonitor=false', '-c',
                      'core.untrackedCache=false', *args], env=env)


def git(root, *args, allow_missing=False):
    result = subprocess.run(**git_command(root, *args), capture_output=True, check=False)
    if allow_missing and result.returncode == 1:
        return b''
    if result.returncode:
        raise MappingError(f'Git {args[0]} failed: {result.stderr.decode("utf-8", "replace").strip()}')
    return result.stdout


def commit_changes(root, base, target):
    """Return paths changed across a proven descendant transition."""
    ancestor = subprocess.run(**git_command(root, 'merge-base', '--is-ancestor', base, target),
                              capture_output=True, check=False)
    if ancestor.returncode:
        return None
    changed = git(root, 'diff', '--no-ext-diff', '--no-textconv', '--no-renames',
                  '--no-relative', '--ignore-submodules=none', '--name-only', '-z', base, target, '--')
    paths = (git_path(raw) for raw in rows_z(changed))
    return {row(path, 'file')['path'] for path in paths if not excluded(path)}


def repository(path):
    root = Path(path).resolve(strict=True)
    top = Path(os.fsdecode(git(root, 'rev-parse', '--show-toplevel').rstrip(b'\r\n'))).resolve(strict=True)
    if root != top:
        raise MappingError(f'use the Git repository root: {top}')
    return root


def linked(info):
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def path_parts(path):
    parts = path.split('/')
    if any(p in {'', '.', '..'} for p in parts):
        raise MappingError('invalid repository-relative path')
    if os.name == 'nt' and any(PurePosixPath(p).name != p or '\\' in p or ':' in p
                              or p.endswith(('.', ' ')) or Path(p).is_reserved() for p in parts):
        raise MappingError('path is unsupported on Windows')
    return parts


def excluded(path):
    return path.split('/', 1)[0].casefold() in {'.project-mapper', '.git'}


def work_path(root, path):
    parts = path_parts(path)
    current = root
    for index, part in enumerate(parts):
        current = current / part
        info = current.lstat()
        if linked(info) or index == len(parts) - 1:
            return current, info
        if not stat.S_ISDIR(info.st_mode):
            raise FileNotFoundError(path)
    raise AssertionError('empty path')


def file_bytes(root, path):
    current, info = work_path(root, path)
    if linked(info) or not stat.S_ISREG(info.st_mode) or current.resolve(strict=True) != current:
        raise MappingError('path is not a regular in-repository file')
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    flags |= getattr(os, 'O_NONBLOCK', 0)
    with os.fdopen(os.open(current, flags), 'rb') as source:
        opened = os.fstat(source.fileno())
        if not os.path.samestat(opened, info) or not stat.S_ISREG(opened.st_mode):
            raise MappingError('file identity changed before read')
        data = source.read()
        checked, after = work_path(root, path)
        if (checked != current or linked(after) or not os.path.samestat(opened, after)
                or opened.st_size != len(data) or opened.st_mtime_ns != after.st_mtime_ns):
            raise MappingError('file identity changed during read')
        return data


def git_path(raw):
    return raw.decode('utf-8', 'surrogateescape')


def rows_z(data):
    return data.rstrip(b'\0').split(b'\0') if data else []


def row(path, kind, content_id=None, status='pending', reason='', tracked=False):
    try:
        path.encode('utf-8')
    except UnicodeEncodeError:
        raw_path = path.encode('utf-8', 'surrogateescape').hex()
        path = ''.join(f'%{ord(ch) - 0xdc00:02X}' if 0xdc80 <= ord(ch) <= 0xdcff
                       else '%25' if ch == '%' else ch for ch in path)
        return dict(path=path, kind=kind, content_id=content_id, eligible=False,
                    status='unsupported', reason='non-UTF-8 Git path (percent-encoded)', tracked=tracked,
                    raw_path=raw_path)
    return dict(path=path, kind=kind, content_id=content_id, eligible=status == 'pending',
                status=status, reason=reason, tracked=tracked)


def commit_entries(root, revision):
    entries = []
    for item in rows_z(git(root, 'ls-tree', '--full-tree', '-rz', revision)):
        head, raw = item.split(b'\t', 1)
        mode, _, oid = head.decode('ascii').split()
        path = git_path(raw)
        kind = {'160000': 'submodule', '120000': 'symlink'}.get(mode, 'file')
        status = 'pending' if kind == 'file' else 'unsupported'
        reason = '' if kind == 'file' else f'{kind} boundary'
        if excluded(path):
            status, reason = 'excluded', 'mapper and Git metadata are outside input scope'
        entries.append(row(path, kind, f'git:{oid}', status, reason, tracked=True))
    return entries


def work_entry(root, path, modes):
    tracked = bool(modes)
    if excluded(path):
        return row(path, 'file', status='excluded', reason='mapper metadata', tracked=tracked)
    if '160000' in modes:
        return row(path, 'submodule', status='unsupported', reason='submodule boundary', tracked=True)
    if '120000' in modes and os.name == 'nt':
        try:
            _, info = work_path(root, path)
            if not linked(info) and stat.S_ISREG(info.st_mode):
                return row(path, 'symlink', status='unsupported',
                           reason='Git symlink stored as a checkout placeholder', tracked=True)
        except OSError:
            pass
    if path.endswith('/'):
        return row(path, 'boundary', status='unsupported', reason='Git reported an embedded repository')
    probe = row(path, 'file', tracked=tracked)
    if 'raw_path' in probe:
        return probe
    try:
        current, info = work_path(root, path)
        if linked(info):
            return row(path, 'symlink', status='unsupported', reason='link boundary', tracked=tracked)
        if not stat.S_ISREG(info.st_mode):
            return row(path, 'special', status='unsupported', reason='non-regular entry', tracked=tracked)
        if current.name == '.git':
            return row(path, 'boundary', status='excluded', reason='Git metadata', tracked=tracked)
        data = file_bytes(root, path)
    except FileNotFoundError:
        return row(path, 'file', status='deleted' if tracked else 'blocked',
                   reason='path missing from working tree', tracked=tracked)
    except (OSError, MappingError):
        return row(path, 'file', status='blocked', reason='unreadable or unstable working-tree entry',
                   tracked=tracked)
    return row(path, 'file', 'sha256:' + hashlib.sha256(data).hexdigest(), tracked=tracked)


def worktree_entries(root):
    tracked = {}
    for item in rows_z(git(root, 'ls-files', '-z', '--stage')):
        head, name = item.split(b'\t', 1)
        tracked.setdefault(name, set()).add(head.decode('ascii').split()[0])
    untracked = rows_z(git(root, 'ls-files', '-z', '--others', '--exclude-standard',
                           '--exclude=/.project-mapper/', '--', '.', ':(exclude).project-mapper'))
    ignored = rows_z(git(root, 'ls-files', '-z', '--others', '--ignored', '--exclude-standard',
                         '--directory', '--no-empty-directory', '--', '.', ':(exclude).project-mapper'))
    entries = [work_entry(root, git_path(raw), tracked.get(raw, set()))
               for raw in sorted(set(tracked) | set(untracked))]
    head = git(root, 'rev-parse', '--verify', '--quiet', 'HEAD', allow_missing=True).decode().strip()
    if head:
        # An index deletion stops qualifying as tracked for ignore selection, but its
        # absent checkout path still needs an outcome.
        deleted = git(root, 'diff-index', '--cached', '--no-ext-diff', '--no-textconv', '--no-renames',
                      '--diff-filter=D', '--name-only', '-z', head, '--')
        for raw in rows_z(deleted):
            path = git_path(raw)
            if excluded(path):
                continue
            try:
                work_path(root, path)
            except FileNotFoundError:
                entries.append(row(path, 'file', status='deleted',
                                   reason='HEAD path deleted from index and working tree', tracked=True))
            except (OSError, MappingError):
                entries.append(row(path, 'file', status='blocked',
                                   reason='could not examine staged deletion', tracked=True))
    for raw in sorted(set(ignored) - set(tracked)):
        path = git_path(raw)
        if not excluded(path):
            entries.append(row(path, 'pruned-directory' if path.endswith('/') else 'ignored',
                               status='excluded', reason='Git standard ignores'))
    return entries


def inventory(root, commit=None):
    revision = None
    if commit is not None:
        revision = git(root, 'rev-parse', '--verify', '--end-of-options', commit + '^{commit}').decode().strip()
        policy = ['Committed Git tree. No Git ignore source applies to tracked entries.']
        entries = commit_entries(root, revision)
    else:
        policy = ['Tracked entries come from the Git index and bypass ignore rules.',
                  'Absent staged HEAD deletions are retained for coverage.',
                  'Untracked entries use Git --exclude-standard.',
                  'Precedence: nested .gitignore (deeper overrides parent), $GIT_DIR/info/exclude, '
                  'core.excludesFile (default $XDG_CONFIG_HOME/git/ignore or ~/.config/git/ignore).']
        entries = worktree_entries(root)
    policy.append('Root .project-mapper/ and .git are excluded from analysis.')
    entries.sort(key=lambda item: (item['path'], item.get('raw_path', '')))
    # Reject an ambiguous display identity instead of merging a path with an encoded spelling.
    if len({item['path'] for item in entries}) != len(entries):
        raise MappingError('inventory path encoding collision')
    snapshot = dict(mode='commit' if revision else 'worktree', revision=revision)
    snapshot['identity'] = digest([snapshot, policy, entries])
    return dict(snapshot=snapshot, ignore_policy=policy, entries=entries)


class SnapshotReader:
    def __init__(self, root, manifest, objects=None):
        self.root = root
        self.entries = {entry['path']: entry for entry in manifest['entries']}
        self.objects = objects
        self.lock = threading.Lock()

    def read(self, path):
        entry = self.entries.get(path)
        if not entry or not entry['eligible']:
            raise MappingError('path is outside eligible inventory')
        method, expected = entry['content_id'].split(':', 1)
        if method == 'git':
            with self.lock:
                self.objects.stdin.write(expected.encode() + b'\n')
                self.objects.stdin.flush()
                header = self.objects.stdout.readline().split()
                if len(header) != 3 or header[:2] != [expected.encode(), b'blob']:
                    raise MappingError('snapshot Git blob is unavailable')
                data = self.objects.stdout.read(int(header[2]))
                if self.objects.stdout.read(1) != b'\n':
                    raise MappingError('snapshot Git blob response is incomplete')
            algorithm = 'sha1' if len(expected) == 40 else 'sha256'
            prefix = f'blob {len(data)}\0'.encode()
        else:
            try:
                data = file_bytes(self.root, path)
            except (OSError, MappingError) as error:
                raise MappingError('snapshot bytes could not be reread') from error
            algorithm, prefix = 'sha256', b''
        if hashlib.new(algorithm, prefix + data).hexdigest() != expected:
            raise MappingError('snapshot content identity mismatch')
        return data


@contextmanager
def snapshot_reader(root, manifest):
    if manifest['snapshot']['mode'] == 'worktree':
        yield SnapshotReader(root, manifest)
    else:
        with subprocess.Popen(**git_command(root, 'cat-file', '--batch'), stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as objects:
            try:
                yield SnapshotReader(root, manifest, objects)
            finally:
                objects.stdin.close()


def snapshot_options(parser):
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--commit', help='Git revision resolved once to a pinned commit')
    modes.add_argument('--worktree', action='store_true', help='explicit working-tree snapshot')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    snapshot_options(parser)
    args = parser.parse_args()
    try:
        print(canonical(inventory(repository(args.repo), args.commit)))
    except (MappingError, OSError) as error:
        parser.exit(1, f'project-mapper: {error}\n')


if __name__ == '__main__':
    main()
