"""Build, publish, inspect and verify a source-backed repository map."""

import argparse
from collections import Counter
from contextlib import closing, contextmanager
from fnmatch import fnmatchcase
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
from uuid import uuid4

sys.dont_write_bytecode = True

import graph_store as store
from investigation import compile_investigation, new_plan, validate_plan, validate_shard
from pipeline import (collect, envelope, final_coverage, load, make_plan, project, review_envelope,
                      reviews, safe_path, save, validate_baseline)
from python_profile import MANIFEST, PROFILE, Source, extract
from scan_files import MappingError, canonical, digest, inventory, repository, snapshot_options, snapshot_reader


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


def start_run(root, commit, *, investigation=False, agent_review=False):
    manifest = inventory(root, commit)
    directory, _, _ = output_paths(root, create=True)
    name = 'run-' + uuid4().hex
    stage = safe_path(directory, name, directory=True, create=True)
    shards = safe_path(stage, 'shards', directory=True, create=True)
    save(safe_path(stage, 'inventory.json'), manifest)
    result = dict(run=name, snapshot=manifest['snapshot'], plan=str(stage / 'plan.json'),
                  inventory=str(stage / 'inventory.json'), shards=str(shards))
    if investigation:
        plan = new_plan(manifest['snapshot']['identity'])
        decisions = safe_path(stage, 'decisions.json')
        save(decisions, {})
        result['decisions'] = str(decisions)
    else:
        with snapshot_reader(root, manifest) as reader:
            plan = make_plan(manifest, reader, agent_review)
            collect(plan, reader, stage)
        result['review_tasks'] = [dict(id=key, path=str(stage / item['output']), dependencies=item['dependencies'])
                                  for key, item in plan['tasks'].items() if key.startswith('review-')]
    save(safe_path(stage, 'plan.json'), plan)
    return result


def load_run(stage, *, allow_legacy=False):
    manifest = load(safe_path(stage, 'inventory.json'))
    plan = load(safe_path(stage, 'plan.json'))
    identity = manifest['snapshot']['identity']
    snapshot = dict(manifest['snapshot'])
    del snapshot['identity']
    if digest([snapshot, manifest['ignore_policy'], manifest['entries']]) != identity:
        raise MappingError('saved inventory fingerprint mismatch')
    if safe_path(stage, 'decisions.json').exists():
        validate_plan(plan, identity, manifest['entries'], allow_legacy=allow_legacy)
    elif plan.get('snapshot') != identity or plan.get('id') != digest({k: v for k, v in plan.items() if k != 'id'}):
        raise MappingError('saved baseline plan fingerprint mismatch')
    return manifest, plan


def question_index(plan):
    return {question['id']: question for question in plan['questions']}


def check_plan(root, name):
    stage = run_directory(output_paths(root)[0], name)
    _, plan = load_run(stage)
    if 'questions' not in plan:
        raise MappingError('check-plan requires a supervisor-led investigation')
    return dict(plan=plan, fingerprint=digest(plan))


def decision_fingerprint(output_language, question, raw, decisions):
    if not isinstance(decisions, dict):
        raise MappingError('decisions must be an object')
    dependencies = {}
    for key in question['depends_on']:
        if key not in decisions:
            raise MappingError(f'review prerequisite question first: {key}')
        dependencies[key] = decisions[key]
    return digest([{'output_language': output_language}, question, raw, dependencies])


def investigation_rows(stage, manifest, plan, reader):
    questions = question_index(plan)
    if not questions:
        raise MappingError('write the investigation questions to plan.json before publishing')
    decisions = load(safe_path(stage, 'decisions.json'))
    if not isinstance(decisions, dict) or decisions.keys() - questions.keys():
        raise MappingError('decisions must map planned question IDs to checked fingerprints')
    shard_paths = safe_path(stage, 'shards', directory=True)
    allowed = {key + '.json' for key in questions}
    if {path.name for path in shard_paths.iterdir()} - allowed:
        raise MappingError('shard directory has outputs without task ownership')
    accepted = {}
    for key, fingerprint in decisions.items():
        raw = load(safe_path(shard_paths, key + '.json'))
        if decision_fingerprint(plan['output_language'], questions[key], raw, decisions) != fingerprint:
            raise MappingError(f'review the current language contract, evidence, question and prerequisites: {key}')
        accepted[key] = raw
    return compile_investigation(manifest, plan, accepted, reader)


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
    if connection.execute('SELECT 1 FROM discoveries LIMIT 1').fetchone():
        commands.extend([f'{prefix} search "<words describing the behavior>" --limit 5',
                         f'{prefix} open "<key from search>"',
                         f'{prefix} trace "<key from search>" --direction both --depth 1'])
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
        *(['- Map language is English. Source identifiers and literals retain their original spelling.']
          if info['plan'].get('output_language') == 'en' else []),
        f'- Coverage {info["status"]}' + (' for the planned questions' if 'investigation_scope' in info else ''),
        *([f'- Cited files {info["investigation_scope"]["cited_files"]} of '
           f'{info["investigation_scope"]["eligible_files"]} eligible files'] if 'investigation_scope' in info else []),
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


def baseline_rows(stage, manifest, plan, reader):
    expected_plan(manifest, plan, reader)
    shard_directory = safe_path(stage, 'shards', directory=True)
    allowed = {Path(item['output']).name for key, item in plan['tasks'].items()
               if key.startswith(('scan-', 'review-'))}
    if {item.name for item in shard_directory.iterdir()} - allowed:
        raise MappingError('shard directory has outputs without task ownership')
    baseline = {key: load(safe_path(stage, item['output'])) for key, item in plan['tasks'].items()
                if key.startswith('scan-')}
    return synthesize(manifest, plan, reader, baseline, reviews(plan, stage, reader))


@contextmanager
def write_lock(directory):
    # Only hold this lock while replacing shared state. The OS releases it on exit or crash.
    for suffix in ('', '-journal', '-wal', '-shm'):
        safe_path(directory, 'publication.sqlite' + suffix)
    with closing(sqlite3.connect(directory / 'publication.sqlite', timeout=10)) as lock:
        lock.execute('BEGIN IMMEDIATE')
        yield


def scope_info(info):
    return {'investigation_scope': info['investigation_scope']} if 'investigation_scope' in info else {}


def guard_promotion(path, info):
    if not path.exists():
        return
    with store.database(path) as current:
        prior = store.metadata(current)
    if prior['snapshot'] != info['snapshot']:
        return
    if 'questions' in prior['plan'] and 'questions' not in info['plan']:
        raise MappingError('active investigation preserved; request Python hints within the investigation')
    proposed_plan = info['plan']
    migrating = ('questions' in prior['plan'] and 'output_language' not in prior['plan']
                 and proposed_plan.get('output_language') == 'en')
    if migrating:
        proposed_plan = {key: value for key, value in proposed_plan.items() if key != 'output_language'}
    same_plan = prior['plan'] == proposed_plan
    # Translation can change question IDs and wording while covering the same snapshot.
    if (migrating or same_plan) and prior['status'] == 'complete' and info['status'] != 'complete':
        raise MappingError('active complete graph preserved; new coverage is partial')
    if same_plan and set(prior.get('accepted_shards', {})) - set(info.get('accepted_shards', {})):
        raise MappingError('active investigation preserved; previously accepted questions are missing')


def publish(root, name, *, reviewed_english_plan=None):
    directory, graph_path, readme_path = output_paths(root)
    stage = run_directory(directory, name)
    manifest, plan = load_run(stage)
    with snapshot_reader(root, manifest) as reader:
        if 'questions' in plan:
            if reviewed_english_plan != digest(plan):
                raise MappingError('review the full current plan with check-plan and pass its fingerprint '
                                   'with --reviewed-english-plan')
            data = investigation_rows(stage, manifest, plan, reader)
        else:
            data = baseline_rows(stage, manifest, plan, reader)
    # A separate publication attempt directory allows retries after a crash or invalid shard.
    attempt = safe_path(stage, 'publish-' + uuid4().hex, directory=True, create=True)
    candidate = safe_path(attempt, 'candidate.sqlite')
    candidate_readme = safe_path(attempt, 'README.md')
    store.write(candidate, data)
    with store.database(candidate) as connection:
        store.check_integrity(connection, data)
        info = store.metadata(connection)
        write_readme(candidate_readme, info, connection, Path(__file__).resolve())
    with write_lock(directory):
        if manifest != inventory(root, manifest['snapshot']['revision']):
            raise MappingError('input snapshot changed before publication')
        if 'questions' in plan and load(safe_path(stage, 'plan.json')) != plan:
            raise MappingError('plan changed during publication; review the current plan with check-plan')
        output_paths(root)
        guard_promotion(graph_path, info)
        os.replace(candidate, graph_path)
        readme_written = True
        try:
            os.replace(candidate_readme, readme_path)
        except OSError:
            readme_written = False
    return dict(path=str(graph_path), snapshot=info['snapshot'], status=info['status'],
                readme_written=readme_written, run=name, **scope_info(info), relationships=len(data['relationships']),
                nodes=len(data['nodes']), discoveries=len(data.get('discoveries', [])),
                supplemental_fingerprint=info['supplemental_fingerprint'])


def verify(root, connection):
    store.check_integrity(connection)
    info = store.metadata(connection)
    manifest = inventory(root, info['snapshot']['revision'])
    if manifest['snapshot'] != info['snapshot']:
        raise MappingError('current input snapshot differs from published graph')
    with snapshot_reader(root, manifest) as reader:
        if 'questions' in info['plan']:
            data = compile_investigation(manifest, info['plan'], info['accepted_shards'], reader, allow_legacy=True)
        else:
            if info['profile'] != PROFILE:
                raise MappingError('recorded Python profile differs; use the original mapper to replay or rebuild')
            reports = {key: json.loads(report) for key, report in connection.execute('SELECT id,report FROM tasks')}
            baseline = {key: value for key, value in reports.items() if key.startswith('scan-')}
            expected_plan(manifest, info['plan'], reader)
            data = synthesize(manifest, info['plan'], reader, baseline, info['supplemental'])
    store.check_integrity(connection, data)
    return dict(snapshot=info['snapshot'], integrity='ok', status=info['status'], **scope_info(info), entries=len(data['inventory']),
                relationships=len(data['relationships']), nodes=len(data['nodes']), discoveries=len(data.get('discoveries', [])))


def worker_prompt(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    manifest, plan = load_run(stage)
    if 'questions' not in plan:
        raise MappingError('worker-prompt requires a supervisor-led investigation')
    question = question_index(plan).get(args.question)
    if question is None:
        raise MappingError('unknown investigation question')
    mapper = Path(__file__).resolve()
    contract = (mapper.parent.parent / 'references' / 'worker.md').read_text(encoding='utf-8').rstrip()
    assignment = dict(root=str(root), mapper=str(mapper), run=args.run, question=question,
                      output_language=plan['output_language'],
                      snapshot=manifest['snapshot']['identity'], plan=str(stage / 'plan.json'),
                      inventory=str(stage / 'inventory.json'),
                      shard=str(safe_path(stage, f'shards/{args.question}.json')))
    prompt = contract + '\n\nAssignment\n' + canonical(assignment)
    if args.repair is not None:
        if not args.repair.strip():
            raise MappingError('a repair requires a concrete diagnostic')
        prompt += '\n\nRepair\n' + canonical({'diagnostic': args.repair})
    return {'prompt': prompt}


def worker_input(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    manifest, plan = load_run(stage, allow_legacy=True)
    with snapshot_reader(root, manifest) as reader:
        if 'questions' in plan:
            if args.task != '@' and args.task not in question_index(plan):
                raise MappingError('unknown investigation question')
        else:
            task = plan['tasks'].get(args.task)
            if not task or not args.task.startswith('review-') or args.path not in task['paths']:
                raise MappingError('input path is outside this worker assignment')
        if args.path not in reader.entries or not reader.entries[args.path]['eligible']:
            raise MappingError('input path is outside eligible inventory')
        source = Source(reader, args.path)
        if args.start < 1 or args.count < 1 or args.count > 120:
            raise MappingError('start must be positive and count must be in 1..120')
        return dict(path=args.path, content_id=source.content_id, start=args.start,
                    total_lines=len(source.lines), lines=[line.decode() for line in
                                                         source.lines[args.start - 1:args.start - 1 + args.count]])


def check_shard(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    manifest, plan = load_run(stage)
    with snapshot_reader(root, manifest) as reader:
        if 'questions' in plan:
            question = question_index(plan).get(args.task)
            if question is None:
                raise MappingError('unknown investigation question')
            raw = load(safe_path(stage, f'shards/{args.task}.json'))
            decisions = load(safe_path(stage, 'decisions.json'))
            validate_shard(question['id'], raw, manifest, reader)
            fingerprint = decision_fingerprint(plan['output_language'], question, raw, decisions)
            return dict(question=args.task, status=raw['status'], claims=len(raw['claims']),
                        discoveries=len(raw.get('discoveries', [])), fingerprint=fingerprint)
        task = plan['tasks'].get(args.task)
        if not task or not args.task.startswith('review-'):
            raise MappingError('task does not own a review shard')
        return review_envelope(plan, args.task, load(safe_path(stage, task['output'])), reader)


def accept_shard(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    path = safe_path(stage, 'decisions.json')
    if not path.is_file():
        raise MappingError('accept applies to supervisor-led investigations')
    with write_lock(stage):
        checked = check_shard(root, args)
        if checked['fingerprint'] != args.fingerprint:
            raise MappingError('reviewed fingerprint changed; reopen the evidence before accepting')
        decisions = load(path)
        decisions[args.task] = args.fingerprint
        temporary = safe_path(stage, f'decisions-{uuid4().hex}.tmp')
        save(temporary, decisions)
        os.replace(temporary, path)
    return checked


def search_inputs(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    manifest, _ = load_run(stage, allow_legacy=True)
    if not args.literal or not 1 <= args.limit <= 500:
        raise MappingError('supply a nonempty literal and a result limit in 1..500')
    needle = args.literal.encode()
    matches, unreadable = [], []
    with snapshot_reader(root, manifest) as reader:
        for path, entry in reader.entries.items():
            if not entry['eligible'] or (args.glob and not any(fnmatchcase(path, pat) for pat in args.glob)):
                continue
            try:
                source = Source(reader, path)
            except (UnicodeError, SyntaxError, LookupError):
                unreadable.append(path)
                continue
            if '\x00' in source.text:
                unreadable.append(path)
                continue
            for line, value in enumerate(source.lines, 1):
                if needle in value:
                    if len(matches) == args.limit:
                        return dict(matches=matches, unreadable=unreadable, truncated=True)
                    matches.append(dict(path=path, content_id=source.content_id, line=line))
    return dict(matches=matches, unreadable=unreadable, truncated=False)


def python_hints(root, args):
    stage = run_directory(output_paths(root)[0], args.run)
    manifest, _ = load_run(stage, allow_legacy=True)
    if not (args.path.endswith('.py') or args.path == MANIFEST):
        raise MappingError('Python hints support .py files and the root pyproject.toml')
    with snapshot_reader(root, manifest) as reader:
        if args.path not in reader.entries or not reader.entries[args.path]['eligible']:
            raise MappingError('input path is outside eligible inventory')
        return extract(reader, args.path)


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path, help='root of the target Git repository')
    commands = parser.add_subparsers(dest='command', required=True)
    snapshot_options(commands.add_parser('investigate', help='start a supervisor-authored mapping plan'))
    snapshot_options(commands.add_parser('build', help='publish the optional static Python baseline'))
    prepare_args = commands.add_parser('prepare', help='inventory, plan and extract in an unpublished run')
    snapshot_options(prepare_args)
    prepare_args.add_argument('--agent-review', action='store_true')
    commands.add_parser('check-plan', help='return the full investigation plan and its fingerprint').add_argument('run')
    publish_args = commands.add_parser('publish', help='validate, resolve and atomically publish a prepared run')
    publish_args.add_argument('run')
    publish_args.add_argument('--reviewed-english-plan', metavar='FINGERPRINT',
                              help='for investigations, confirm English review of every question in this exact plan')
    worker = commands.add_parser('worker-prompt', help='render a single isolated worker assignment')
    worker.add_argument('run')
    worker.add_argument('question')
    worker.add_argument('--repair', help='append one retry diagnostic to this assignment')
    read = commands.add_parser('read-input', help='read a checked, assigned worker locator')
    read.add_argument('run')
    read.add_argument('task')
    read.add_argument('path')
    read.add_argument('--start', type=int, default=1)
    read.add_argument('--count', type=int, default=40)
    search = commands.add_parser('search-input', help='find a literal in eligible snapshot text')
    search.add_argument('run')
    search.add_argument('literal')
    search.add_argument('--glob', action='append', default=[])
    search.add_argument('--limit', type=int, default=50)
    hints = commands.add_parser('hints', help='inspect optional Python extractor candidates for one input')
    hints.add_argument('run')
    hints.add_argument('path')
    check = commands.add_parser('check-shard', help='validate an assigned worker shard before publication')
    check.add_argument('run')
    check.add_argument('task')
    accept = commands.add_parser('accept', help='record the supervisor decision for an exact checked shard')
    accept.add_argument('run')
    accept.add_argument('task')
    accept.add_argument('fingerprint')
    accept.add_argument('--reviewed-english', action='store_true', required=True,
                        help='confirm the question and authored findings are in English and source literals are exact')
    coverage = commands.add_parser('coverage', help='show coverage, ignore policy and discrepancies')
    coverage.add_argument('--family')
    coverage.add_argument('--area')
    commands.add_parser('dimensions', help='show evidence-backed memberships')
    lookup = commands.add_parser('search', help='locate reviewed discoveries by words in their index')
    lookup.add_argument('query')
    lookup.add_argument('--limit', type=int, default=5, help='maximum candidates returned (1..100)')
    commands.add_parser('open', help='read one discovery and its supporting evidence by exact ID').add_argument('key')
    commands.add_parser('node', help='look up a node by key or exact name').add_argument('selector')
    trace = commands.add_parser('trace', help='traverse typed edges and show incomplete frontiers')
    trace.add_argument('selector')
    trace.add_argument('--direction', choices=['in', 'out', 'both'], default='out')
    trace.add_argument('--type', action='append', default=[], help='repeat for each relationship type')
    trace.add_argument('--depth', type=int, default=4)
    trace.add_argument('--max-nodes', type=int, default=100)
    trace.add_argument('--max-edges', type=int, default=250)
    commands.add_parser('verify', help='check schema, source identity and independently replay claims')
    return parser, parser.parse_args()


def dispatch(root, args):
    if args.command == 'investigate':
        return start_run(root, args.commit, investigation=True)
    if args.command == 'build':
        return publish(root, start_run(root, args.commit)['run'])
    if args.command == 'prepare':
        return start_run(root, args.commit, agent_review=args.agent_review)
    if args.command == 'check-plan':
        return check_plan(root, args.run)
    if args.command == 'publish':
        return publish(root, args.run, reviewed_english_plan=args.reviewed_english_plan)
    if args.command == 'worker-prompt':
        return worker_prompt(root, args)
    if args.command == 'read-input':
        return worker_input(root, args)
    if args.command == 'search-input':
        return search_inputs(root, args)
    if args.command == 'hints':
        return python_hints(root, args)
    if args.command == 'accept':
        return accept_shard(root, args)
    if args.command == 'check-shard':
        return check_shard(root, args)
    with store.database(output_paths(root)[1]) as connection:
        store.check_schema(connection)
        if args.command == 'coverage':
            return store.inspect_coverage(connection, args.family, args.area)
        if args.command == 'dimensions':
            return dict(memberships=store.dimensions(connection))
        if args.command == 'search':
            matches = store.search_discoveries(connection, args.query, args.limit)
            return dict(snapshot=store.metadata(connection, 'snapshot')['snapshot'], matches=matches)
        if args.command == 'open':
            discovery = store.open_discovery(connection, args.key)
            return dict(snapshot=store.metadata(connection, 'snapshot')['snapshot'], **discovery)
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
