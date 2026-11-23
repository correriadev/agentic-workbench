"""Isolated trial setup and timestamped CLI proxy. Run each trial with a single investigator."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time


REV = '97f10e8957811bcabd8393d2dd2f2427d7ee9388'
QUESTIONS = {
    'manifest': ('Which website workflow records and checks the published revision?',
                 ['.github/workflows/website-pages.yml'],
                 ['Trace the prepublication check to its concrete script.',
                  'Trace the revision value to its generated file.',
                  'Trace the generated file into the delivery archive.',
                  'Identify the verification comparison and its host conditions.']),
    'zip': ('How does the website’s downloadable Notes Electron example ZIP move from source files through '
            'generation and verification to the checked website artifact, and what does the repository establish '
            'about verification of the published ZIP?', ['.github/workflows/website-pages.yml'],
            ['Identify the relevant build and verification entry path and order.',
             'Trace inputs to the produced archive and distinguish selected contents from archive metadata.',
             'Trace the archive and its comparison inputs into validation and explain the acceptance/failure cases.',
             'Trace the checked artifact through its publishing handoff and delimit what the repository’s '
             'post-publication checks establish.'])}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def record(root, event, **data):
    with (root/'events.jsonl').open('a', encoding='utf-8') as stream:
        print(json.dumps(dict(time=now(), event=event, **data)), file=stream)


def setup(source, mapper, output, case, arm):
    root, source, mapper = map(lambda p: Path(p).resolve(), (output, source, mapper))
    if root.is_relative_to(source) or arm not in ('A', 'B'):
        raise ValueError('expected fresh external directory and A or B')
    root.mkdir(parents=True, exist_ok=False)
    subprocess.run(['git', 'clone', '-q', '--shared', '--no-checkout', str(source), str(root)], check=True)
    def cli(*args):
        return json.loads(subprocess.check_output([sys.executable, '-B', str(mapper), str(root), *args]))
    run = cli('investigate', '--commit', REV)
    path = Path(run['plan'])
    plan = json.loads(path.read_text())
    question, seeds, facets = QUESTIONS[case]
    item = dict(id=case, question=question+' '+' '.join(facets), seeds=seeds, depends_on=[])
    if arm == 'B':
        item['question'] = question
        item['required_relations'] = facets
    plan['questions'].append(item)
    path.write_text(json.dumps(plan))
    prompt = cli('worker-prompt', run['run'], case)['prompt']
    proxy = str(Path(__file__).resolve())
    # Replace the executable path in the JSON assignment, preserving the native worker contract.
    prefix, assignment = prompt.rsplit('\nAssignment\n', 1)
    assignment = json.loads(assignment)
    assignment['mapper'] = proxy
    (root/'assignment.txt').write_text(prefix+'\nAssignment\n'+json.dumps(assignment), encoding='utf-8')
    state = dict(mapper=str(mapper), run=run['run'], question=case, shard=assignment['shard'])
    (root/'trial.json').write_text(json.dumps(state))
    record(root, 'ready')


def proxy(root, cmd, args):
    state = json.loads((root/'trial.json').read_text())
    if cmd == 'mark':
        event, = args
        if event not in ('dispatch', 'start', 'submit', 'review', 'reject', 'repair-start'):
            raise ValueError('unknown trial marker')
        if event == 'submit':
            # Preserve the exact first submission even if the worker later repairs its owned shard.
            name = f'submission-{time.time_ns()}.json'
            (root/name).write_bytes(Path(state['shard']).read_bytes())
            record(root, event, copy=name)
        else:
            record(root, event)
        return
    started = now()
    process = subprocess.run([sys.executable, '-B', state['mapper'], str(root), cmd, *args], capture_output=True)
    data = dict(start=started, code=process.returncode)
    if not process.returncode and cmd == 'read-input':
        result = json.loads(process.stdout)
        pages = result.get('pages', [result])
        data['pages'] = [[p['path'], p['content_id'], p['start'], p['start']+len(p['lines'])-1] for p in pages]
    if cmd == 'preflight':
        # Keep the result (or diagnostic) to distinguish preventive checks from worker-authored corrections.
        data['feedback'] = (process.stderr or process.stdout).decode('utf-8').strip()
    record(root, cmd, **data)
    sys.stdout.buffer.write(process.stdout)
    sys.stderr.buffer.write(process.stderr)
    raise SystemExit(process.returncode)


def summarize(root):
    events = [json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
    submissions = []
    valid = None
    for event in events:
        if event['event'] == 'submit':
            submissions.append(json.loads((root/event['copy']).read_text(encoding='utf-8-sig')))
        if event['event'] == 'check-shard' and not event['code']:
            valid = submissions[-1]
    locators = []
    if valid:
        groups = list(valid['claims']) + [valid.get('absence', {})]
        for discovery in valid.get('discoveries', []):
            groups.extend(discovery['support'])
        locators = [ref for group in groups for ref in group.get('evidence', [])]
    first_evidence = None
    pages = 0
    for event in events:
        for path, blob, start, end in event.get('pages', []):
            pages += 1
            if first_evidence is None:
                first_evidence = next((dict(time=event['time'], locator=ref) for ref in locators
                                       if (path, blob) == (ref['path'], ref['content_id'])
                                       and start <= ref['start'] <= ref['end'] <= end), None)
    timeline = []
    for event in events:
        if event['event'] == 'read-input':
            continue
        timeline.append({k: event[k] for k in ('event', 'time', 'start', 'code') if k in event})
    def seconds(a, b):
        return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds()

    durations = {}
    milestones = {'dispatch': 'queue', 'start': 'investigation', 'submit': 'awaiting_review',
                  'review': 'review', 'reject': 'awaiting_repair', 'repair-start': 'rework',
                  'accept': 'publication_and_verification', 'verify': 'awaiting_followup_audit'}
    previous = None
    dispatch = None
    acceptance = None
    first_acceptance = None
    for event in timeline:
        name = event['event']
        if name not in milestones or event.get('code', 0):
            continue
        if previous:
            phase = milestones[previous['event']]
            durations[phase] = durations.get(phase, 0) + seconds(previous['time'], event['time'])
        previous = event
        if name == 'dispatch':
            dispatch = event['time']
        if name == 'accept':
            acceptance = seconds(dispatch, event['time'])
            if first_acceptance is None:
                first_acceptance = acceptance
    overhead = sum(seconds(e['start'], e['time']) for e in timeline if e['event'] == 'preflight')
    return dict(trial=root.name, pages=pages, first_later_validated_evidence=first_evidence,
                seconds_to_first_accept=first_acceptance, seconds_to_last_accept=acceptance,
                phase_seconds=durations, preflight_seconds=overhead,
                timeline=timeline)


if __name__ == '__main__':
    if sys.argv[1] == 'setup':
        setup(*sys.argv[2:])
    elif sys.argv[1] == 'summary':
        print(json.dumps([summarize(Path(path)) for path in sys.argv[2:]], indent=2))
    else:
        proxy(Path(sys.argv[1]), sys.argv[2], sys.argv[3:])
