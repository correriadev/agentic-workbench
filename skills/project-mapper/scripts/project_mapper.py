"""Build, publish, inspect and verify a source-backed repository map."""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
from uuid import uuid4

sys.dont_write_bytecode = True

import graph_store as store
from pipeline import (collect, envelope, final_coverage, load, make_plan, project, review_envelope,
                      reviews, safe_path, save, validate_baseline)
from python_profile import PROFILE, Source
from scan_files import MappingError, canonical, inventory, repository, snapshot_options, snapshot_reader


OUTPUT = '.project-mapper'
RUN = re.compile(r'run-[0-9a-f]{32}\Z')


def output_paths(root, *, create=False):
    directory = safe_path(root, OUTPUT, directory=True, create=create)
    for file in ('graph.sqlite', 'README.md', 'graph.sqlite-journal', 'graph.sqlite-wal', 'graph.sqlite-shm'):
        path = safe_path(directory, file)
        if file.startswith('graph.sqlite-') and path.exists():
            raise MappingError('output graph has a SQLite sidecar; close external writers first')
    return directory, directory / 'graph.sqlite', directory / 'README.md'


def run_directory(directory, name):
    if not RUN.fullmatch(name):
        raise MappingError('invalid run ID')
    stage = safe_path(directory, name, directory=True)
    if not stage.is_dir():
        raise MappingError('run directory is unavailable')
    return stage


def prepare(root, commit, agent_review):
    manifest = inventory(root, commit)
    with snapshot_reader(root, manifest) as reader:
        plan = make_plan(manifest, reader, agent_review)
        directory, _, _ = output_paths(root, create=True)
        name = 'run-' + uuid4().hex
        stage = safe_path(directory, name, directory=True, create=True)
        safe_path(stage, 'shards', directory=True, create=True)
        save(safe_path(stage, 'inventory.json'), manifest)
        save(safe_path(stage, 'plan.json'), plan)
        collect(plan, reader, stage)
    return dict(run=name, snapshot=manifest['snapshot'], plan=str(stage / 'plan.json'),
                inventory=str(stage / 'inventory.json'),
                review_tasks=[dict(id=key, path=str(stage / item['output']), dependencies=item['dependencies'])
                              for key, item in plan['tasks'].items() if key.startswith('review-')])


def reload_run(root, stage):
    saved = load(safe_path(stage, 'inventory.json'))
    manifest = inventory(root, saved['snapshot']['revision'])
    if saved != manifest:
        raise MappingError('input snapshot changed since inventory; prepare a new run')
    plan = load(safe_path(stage, 'plan.json'))
    return manifest, plan


def expected_plan(manifest, plan, reader):
    if plan != make_plan(manifest, reader, plan['agent_review']):
        raise MappingError('saved plan does not match inventory and profile')


def replay_reviews(plan, supplemental, reader):
    keys = {key for key in plan['tasks'] if key.startswith('review-')}
    if keys != set(supplemental):
        raise MappingError('supplemental task coverage mismatch')
    for key, row in supplemental.items():
        if row == dict(task=key, status='unexamined', inputs=[], observations=[]):
            continue
        if row == dict(task=key, status='blocked', inputs=[], observations=[],
                       reason='supplemental shard failed validation'):
            continue
        data = dict(plan=plan['id'], task=key, snapshot=plan['snapshot'], status=row['status'],
                    inputs=row['inputs'], findings=[
                        dict(path=obs['path'], content_id=obs['content_id'], line=obs['span'][0],
                             kind=obs['symbol']) for obs in row['observations']])
        if review_envelope(plan, key, data, reader) != row:
            raise MappingError('supplemental observations do not reproduce from source')


def synthesize(manifest, plan, reader, baseline, supplemental):
    expected = {key for key in plan['tasks'] if key.startswith('scan-')}
    if expected != set(baseline):
        raise MappingError('baseline shard coverage mismatch')
    outcomes = {}
    for key, shard in sorted(baseline.items()):
        outcomes.update(validate_baseline(plan, key, shard, reader))
    replay_reviews(plan, supplemental, reader)
    graph = project(outcomes, supplemental)
    coverage = final_coverage(plan, manifest, outcomes, graph, supplemental)
    gaps = [dict(area=row['area'], family=row['family'], task=row['task'], reason=row['reason'],
                 next_input='review assigned paths or extend the active profile')
            for row in coverage if row['status'] not in {'analyzed', 'excluded', 'inapplicable'}]
    reports = {**baseline, **supplemental,
               'reconcile': dict(envelope(plan, 'reconcile'), relationships=len(graph.relationships),
                                 nodes=len(graph.nodes), cross_area_dependencies=plan['tasks']['reconcile']['dependencies']),
               'frontier': dict(envelope(plan, 'frontier'), gaps=gaps)}
    return store.records(manifest, plan, graph, coverage, outcomes, reports, supplemental)


def write_readme(path, info, connection, script):
    gaps = [row for row in store.coverage_records(connection)
            if row['status'] not in {'analyzed', 'excluded', 'inapplicable'}]
    counts = Counter(row['status'] for row in gaps)
    dims = [name for name, in connection.execute('SELECT DISTINCT dimension FROM memberships ORDER BY dimension')]
    item = connection.execute('SELECT source,type FROM relationships WHERE state=? ORDER BY '
                              "CASE WHEN type='calls' THEN 0 ELSE 1 END,id LIMIT 1", ('resolved',)).fetchone()
    prefix = f'python "{script.as_posix()}" .'
    commands = [f'{prefix} coverage', f'{prefix} dimensions', f'{prefix} verify']
    if item:
        commands.extend([f'{prefix} node "{item["source"]}"',
                         f'{prefix} trace "{item["source"]}" --type {item["type"]} --direction both'])
    snapshot = info['snapshot']
    fence = chr(96) * 3
    content = [
        '# Project Mapper', '',
        f'- Source mode {snapshot["mode"]}',
        f'- Revision or worktree fingerprint {snapshot["revision"] or snapshot["identity"]}',
        f'- Inventory fingerprint {snapshot["identity"]}',
        f'- Profile {info["profile"]["name"]} v{info["profile"]["version"]}',
        f'- Coverage {info["status"]}',
        '- Dimensions ' + (', '.join(dims) or 'none identified'),
        '- Coverage gaps ' + (', '.join(f'{status} ({count})' for status, count in sorted(counts.items())) or 'none'),
        '', '## Material gaps', '',
        *[f'- {row["area"]} / {row["family"]} — {row["reason"]}' for row in gaps[:12]],
        '' if gaps else 'No incomplete coverage assignments.', '',
        '## Inspect from the repository root', '', fence + 'text', *commands, fence, '',
        'SQLite is authoritative for the snapshot and coverage. The coverage command lists every assignment.', '',
    ]
    with path.open('x', encoding='utf-8', newline='\n') as output:
        output.write('\n'.join(content))


def publish(root, name):
    directory, graph_path, readme_path = output_paths(root)
    stage = run_directory(directory, name)
    manifest, plan = reload_run(root, stage)
    with snapshot_reader(root, manifest) as reader:
        expected_plan(manifest, plan, reader)
        shard_directory = safe_path(stage, 'shards', directory=True)
        allowed = {Path(item['output']).name for key, item in plan['tasks'].items()
                   if key.startswith(('scan-', 'review-'))}
        if {item.name for item in shard_directory.iterdir()} - allowed:
            raise MappingError('shard directory has outputs without task ownership')
        baseline = {key: load(safe_path(stage, item['output'])) for key, item in plan['tasks'].items()
                    if key.startswith('scan-')}
        supplemental = reviews(plan, stage, reader)
        data = synthesize(manifest, plan, reader, baseline, supplemental)
    # A separate publication attempt directory allows retries after a crash or invalid shard.
    attempt = safe_path(stage, 'publish-' + uuid4().hex, directory=True, create=True)
    candidate = safe_path(attempt, 'candidate.sqlite')
    candidate_readme = safe_path(attempt, 'README.md')
    store.write(candidate, data)
    with store.database(candidate) as connection:
        store.check_integrity(connection, data)
        info = store.metadata(connection)
        write_readme(candidate_readme, info, connection, Path(__file__).resolve())
    if manifest != inventory(root, manifest['snapshot']['revision']):
        raise MappingError('input snapshot changed before publication')
    output_paths(root)
    os.replace(candidate, graph_path)
    readme_written = True
    try:
        os.replace(candidate_readme, readme_path)
    except OSError:
        readme_written = False
    return dict(path=str(graph_path), snapshot=info['snapshot'], status=info['status'],
                readme_written=readme_written, run=name, relationships=len(data['relationships']),
                nodes=len(data['nodes']), supplemental_fingerprint=info['supplemental_fingerprint'])


def verify(root, connection):
    store.check_integrity(connection)
    info = store.metadata(connection)
    manifest = inventory(root, info['snapshot']['revision'])
    if manifest['snapshot'] != info['snapshot']:
        raise MappingError('current input snapshot differs from published graph')
    reports = {key: json.loads(report) for key, report in connection.execute('SELECT id,report FROM tasks')}
    baseline = {key: value for key, value in reports.items() if key.startswith('scan-')}
    with snapshot_reader(root, manifest) as reader:
        expected_plan(manifest, info['plan'], reader)
        data = synthesize(manifest, info['plan'], reader, baseline, info['supplemental'])
    store.check_integrity(connection, data)
    return dict(snapshot=info['snapshot'], integrity='ok', status=info['status'], entries=len(data['inventory']),
                relationships=len(data['relationships']), nodes=len(data['nodes']))


def worker_input(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    manifest, plan = reload_run(root, stage)
    with snapshot_reader(root, manifest) as reader:
        expected_plan(manifest, plan, reader)
        task = plan['tasks'].get(args.task)
        if not task or not args.task.startswith('review-') or args.path not in task['paths']:
            raise MappingError('input path is outside this worker assignment')
        source = Source(reader, args.path)
        if args.start < 1 or args.count < 1 or args.count > 120:
            raise MappingError('start must be positive and count must be in 1..120')
        return dict(path=args.path, content_id=source.content_id, start=args.start,
                    total_lines=len(source.lines), lines=[line.decode() for line in
                                                         source.lines[args.start - 1:args.start - 1 + args.count]])


def check_shard(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    manifest, plan = reload_run(root, stage)
    with snapshot_reader(root, manifest) as reader:
        expected_plan(manifest, plan, reader)
        task = plan['tasks'].get(args.task)
        if not task or not args.task.startswith('review-'):
            raise MappingError('task does not own a review shard')
        return review_envelope(plan, args.task, load(safe_path(stage, task['output'])), reader)


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path, help='root of the target Git repository')
    commands = parser.add_subparsers(dest='command', required=True)
    snapshot_options(commands.add_parser('build', help='run all six stages locally'))
    prepare_args = commands.add_parser('prepare', help='inventory, plan and extract in an unpublished run')
    snapshot_options(prepare_args)
    prepare_args.add_argument('--agent-review', action='store_true')
    commands.add_parser('publish', help='validate, resolve and atomically publish a prepared run').add_argument('run')
    read = commands.add_parser('read-input', help='read a checked, assigned worker locator')
    read.add_argument('run')
    read.add_argument('task')
    read.add_argument('path')
    read.add_argument('--start', type=int, default=1)
    read.add_argument('--count', type=int, default=40)
    check = commands.add_parser('check-shard', help='validate an assigned worker shard before publication')
    check.add_argument('run')
    check.add_argument('task')
    coverage = commands.add_parser('coverage', help='show coverage, ignore policy and discrepancies')
    coverage.add_argument('--family')
    coverage.add_argument('--area')
    commands.add_parser('dimensions', help='show evidence-backed memberships')
    commands.add_parser('node', help='look up a node by typed key or exact name').add_argument('selector')
    trace = commands.add_parser('trace', help='traverse typed edges and show incomplete frontiers')
    trace.add_argument('selector')
    trace.add_argument('--direction', choices=['in', 'out', 'both'], default='out')
    trace.add_argument('--type', action='append', default=[], choices=sorted(
        kind for kinds in PROFILE['edge_types'].values() for kind in kinds))
    trace.add_argument('--depth', type=int, default=4)
    trace.add_argument('--max-nodes', type=int, default=100)
    trace.add_argument('--max-edges', type=int, default=250)
    commands.add_parser('verify', help='check schema, source identity and independently replay claims')
    return parser, parser.parse_args()


def dispatch(root, args):
    if args.command == 'build':
        return publish(root, prepare(root, args.commit, False)['run'])
    if args.command == 'prepare':
        return prepare(root, args.commit, args.agent_review)
    if args.command == 'publish':
        return publish(root, args.run)
    if args.command == 'read-input':
        return worker_input(root, args)
    if args.command == 'check-shard':
        return check_shard(root, args)
    with store.database(output_paths(root)[1]) as connection:
        store.check_schema(connection)
        if args.command == 'coverage':
            return store.inspect_coverage(connection, args.family, args.area)
        if args.command == 'dimensions':
            return dict(memberships=store.dimensions(connection))
        if args.command == 'node':
            return dict(nodes=store.inspect_node(connection, args.selector))
        if args.command == 'trace':
            if not 0 <= args.depth <= 100 or not 1 <= args.max_nodes <= 10000 or not 1 <= args.max_edges <= 20000:
                raise MappingError('trace bounds outside depth 0..100, nodes 1..10000 or edges 1..20000')
            return store.trace(connection, args.selector, args.direction, args.type, args.depth,
                               args.max_nodes, args.max_edges)
        return verify(root, connection)


def main():
    parser, args = arguments()
    try:
        print(canonical(dispatch(repository(args.repo), args)))
    except (MappingError, OSError, sqlite3.Error, ValueError, KeyError, TypeError, LookupError, SyntaxError) as error:
        parser.exit(1, f'project-mapper: {error}\n')


if __name__ == '__main__':
    main()
