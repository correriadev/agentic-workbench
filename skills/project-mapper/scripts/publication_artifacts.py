"""Own and discard transient publication files under the publication lock."""

from contextlib import contextmanager
import re
import shutil
import sqlite3
import stat
from uuid import uuid4

import graph_store
from pipeline import load, safe_path, save
from scan_files import MappingError, linked


STAGE = re.compile(r'staging-[0-9a-f]{32}\Z')
ATTEMPT = re.compile(r'publish-[0-9a-f]{32}\Z')
RUN = re.compile(r'run-[0-9a-f]{32}\Z')
OWNER = 'owner.json'
CANDIDATES = {OWNER, 'candidate.sqlite', 'README.md', 'cache.sqlite'}
RUN_FILES = {'inventory.json', 'plan.json', 'decisions.json', 'static-profile.json',
             'graph-pin.json', 'prior-review.json', 'shards'}
PIN_TEMP = re.compile(r'graph-pin-[0-9a-f]{32}\.tmp\Z')
SQLITE_SIDECARS = {name + suffix for name in ('candidate.sqlite', 'cache.sqlite')
                   for suffix in ('-journal', '-wal', '-shm')}


def regular_tree(path):
    info = path.lstat()
    if linked(info):
        return False
    if stat.S_ISDIR(info.st_mode):
        return all(regular_tree(child) for child in path.iterdir())
    return stat.S_ISREG(info.st_mode) and info.st_nlink == 1


def owned_stage(path):
    try:
        if not path.is_dir() or not regular_tree(path):
            return False
        if load(safe_path(path, OWNER)) != {'publication_workspace': path.name}:
            return False
        return all(
            (child.is_file() and child.name in CANDIDATES | SQLITE_SIDECARS)
            or (child.is_dir() and child.name == 'shards'
                and all(item.is_file() and item.name.startswith('scan-') and item.suffix == '.json'
                        for item in child.iterdir()))
            or (child.is_dir() and RUN.fullmatch(child.name)
                and all(item.name in RUN_FILES or PIN_TEMP.fullmatch(item.name) for item in child.iterdir()))
            for child in path.iterdir()
        )
    except (OSError, ValueError, MappingError, RecursionError):
        return False


def abandoned_stages(directory, *, current=None):
    return [path for path in sorted(directory.iterdir())
            if path != current and STAGE.fullmatch(path.name) and owned_stage(path)]


def remove_abandoned(directory, *, current=None):
    paths = abandoned_stages(directory, current=current)
    for path in paths:
        shutil.rmtree(path)
    return [path.name for path in paths]


@contextmanager
def publication_workspace(directory):
    name = 'staging-' + uuid4().hex
    path = safe_path(directory, name, directory=True, create=True)
    save(safe_path(path, OWNER), {'publication_workspace': name})
    try:
        yield path
    finally:
        if owned_stage(path):
            # If a filesystem keeps a handle open, the next operation can retry.
            shutil.rmtree(path, ignore_errors=True)


def legacy_attempt(path, snapshot):
    try:
        if not ATTEMPT.fullmatch(path.name) or not path.is_dir() or not regular_tree(path):
            return False
        names = {child.name for child in path.iterdir()}
        if not names <= {'candidate.sqlite', 'README.md'}:
            return False
        if 'candidate.sqlite' in names:
            with graph_store.database(safe_path(path, 'candidate.sqlite')) as graph:
                graph_store.check_schema(graph)
                if graph_store.metadata(graph, 'snapshot').get('snapshot') != snapshot:
                    return False
        if 'README.md' in names:
            with safe_path(path, 'README.md').open(encoding='utf-8') as readme:
                expected = ['# Project Mapper', '', f"- Source mode {snapshot['mode']}",
                            f"- Revision or worktree fingerprint {snapshot['revision'] or snapshot['identity']}",
                            f"- Inventory fingerprint {snapshot['identity']}"]
                if any(readme.readline(256).rstrip('\r\n') != line for line in expected):
                    return False
        return True
    except (OSError, ValueError, MappingError, RecursionError, sqlite3.Error):
        return False


def legacy_artifacts(directory, active_run, load_run):
    """Find static runs and verified publication leftovers from older mappers."""
    candidates = []
    for run in sorted(directory.iterdir()):
        if not RUN.fullmatch(run.name) or not run.is_dir():
            continue
        try:
            stage = safe_path(directory, run.name, directory=True)
            manifest, plan = load_run(stage, allow_legacy=True)
            attempts = [path for path in sorted(stage.iterdir())
                        if legacy_attempt(path, manifest['snapshot'])]
            children = {path.name for path in stage.iterdir()}
            recorded = {'inventory.json', 'plan.json', 'publication.sqlite', 'shards'}
            if (plan.get('kind') == 'multidimensional' and run.name != active_run and attempts
                    and children <= recorded | {path.name for path in attempts}
                    and (stage / 'shards').is_dir() and not any((stage / 'shards').iterdir())
                    and regular_tree(stage)):
                candidates.append(stage)
            else:
                candidates.extend(attempts)
        except (OSError, ValueError, KeyError, TypeError, MappingError, RecursionError):
            continue
    return candidates
