"""Controlled REA source-reading benchmark. Never run a mapper command on the input checkout."""
import argparse
from collections import Counter
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request


REV = '97f10e8957811bcabd8393d2dd2f2427d7ee9388'
NOTES = 'website/public/examples/notes-web/'
QUESTION = 'Which website Pages workflow records and checks the published revision?'
# Only public workflow filenames from the pinned inventory are eligible for external ranking.
SHORTLIST = {'ci.yml', 'ci-full-pr.yml', 'pages.yml', 'website-pages.yml', 'website-check.yml',
             'release.yml', 'release-recovery.yml', 'release-abandon.yml'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def ranked(paths, live, stats):
    words = set(re.findall(r'[a-z]+', QUESTION.lower()))
    paths = sorted(paths, key=lambda p: (-len(words.intersection(re.findall('[a-z]+', Path(p).stem))), p))
    if not live:
        return paths
    keys = {f'p{i}': path for i, path in enumerate(paths)}
    body = json.dumps(dict(model='jev-latest', state={'query': QUESTION}, questions={'next': {
        'type': 'choice', 'instructions': 'Which workflow filename best matches the query?',
        'criteria': keys}})).encode()
    stats.update(request_bytes=len(body), attempted=0, applied=0, replay=0)
    key = os.getenv('TYPESAFE_API_KEY')
    if not key:
        stats['fallback'] = 'missing secret'
        return paths
    start = time.perf_counter()
    try:
        req = urllib.request.Request('https://api.typesafe.ai/v1/systemone', data=body,
                                     headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        stats['attempted'] = 1
        with urllib.request.build_opener(NoRedirect).open(req, timeout=5) as response:
            data = response.read(65537)
        stats['response_bytes'] = len(data)
        if len(data) > 65536:
            raise ValueError('oversized response')
        decoded = json.loads(data)
        answer = decoded['answers']['next']
        scores = answer['probabilities']
        if (answer['type'] != 'choice' or scores.keys() != keys.keys()
                or any(type(v) not in (float, int) or not math.isfinite(v) or not 0 <= v <= 1
                       for v in scores.values())):
            raise ValueError('invalid choice')
        paths = [keys[k] for k in sorted(keys, key=scores.get, reverse=True)]
        stats['applied'] = 1
        usage = decoded.get('usage', {})
        if isinstance(usage, dict):
            stats['usage'] = {k: v for k, v in usage.items() if isinstance(v, (float, int))}
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        stats['fallback'] = f'HTTP {exc.code}' if isinstance(exc, urllib.error.HTTPError) else type(exc).__name__
    stats['seconds'] = time.perf_counter() - start
    return paths


def run(args):
    repo = args.output.resolve()
    if repo.is_relative_to(args.source.resolve()):
        raise ValueError('output must be outside the source checkout')
    repo.mkdir(parents=True, exist_ok=False)
    subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-checkout', str(args.source.resolve()), str(repo)],
                   check=True)
    times, calls, provider = Counter(), Counter(), {}

    def cli(command, *rest):
        begin = time.perf_counter()
        data = subprocess.check_output([sys.executable, str(args.mapper.resolve()), str(repo), command, *map(str, rest)])
        times[command] += time.perf_counter() - begin
        calls[command] += 1
        return json.loads(data)

    start = time.perf_counter()
    run = cli('investigate', '--commit', REV)
    rid = run['run']
    plan_path = Path(run['plan'])
    plan = json.loads(plan_path.read_text())
    expected = []
    all_pages = []

    def investigate(qid, question, seed, stages, rules):
        plan['questions'].append(dict(id=qid, question=question, seeds=seed, depends_on=[]))
        plan_path.write_text(json.dumps(plan), encoding='utf-8')
        cli('worker-prompt', rid, qid)
        locators = []
        for stage in stages:
            pages = []
            if args.arm == 'A':
                for path, line, count, _ in stage:
                    pages.append(cli('read-input', rid, qid, path, '--start', line, '--count', count))
            else:
                path, line, count, _ = stage[0]
                extra = [v for p, l, c, _ in stage[1:] for v in ('--also', p, l, c)]
                result = cli('read-input', rid, qid, path, '--start', line, '--count', count, *extra)
                pages = result['pages'] if extra else [result]
            for page, (path, line, count, needles) in zip(pages, stage, strict=True):
                content = '\n'.join(page['lines'])
                if page['path'] != path or page['start'] != line or any(n not in content for n in needles):
                    raise ValueError(f'unsupported observation at {path}:{line}')
                locators.append(dict(path=path, start=line, end=line+len(page['lines'])-1,
                                     content_id=page['content_id']))
                all_pages.append(locators[-1])
        claims = []
        for source, relation, target, condition, indexes in rules:
            claims.append(dict(source=source, relation=relation, target=target, condition=condition,
                               evidence=[locators[i] for i in indexes]))
            expected.append((source, relation, target))
        shard = Path(run['shards']) / (qid+'.json')
        shard.write_text(json.dumps(dict(snapshot=plan['snapshot'], question=qid, status='answered',
                                         gap='', claims=claims)), encoding='utf-8')
        checked = cli('check-shard', rid, qid)
        cli('accept', rid, qid, checked['fingerprint'], '--reviewed-english')

    if args.slice in ('dev', 'resume'):
        html, js, notes = [NOTES+n for n in ('index.html', 'export.js', 'notes.json')]
        investigate('notes', 'How does the export button turn stored notes into a CSV download?', [html], [
            [(html, 14, 1, ['src="export.js"']), (html, 31, 1, ['id="export"'])],
            [(js, 1, 7, ['#export', 'fetch("./notes.json")', 'response.ok', 'response.json()']),
             (js, 8, 11, ['replaceAll', 'note.id', 'note.title', 'text/csv', 'notes.csv', 'link.click()'])],
            [(notes, 1, 6, ['"notes"', '"id"', '"title"'])]], [
                ('file:'+html, 'loads', 'file:'+js, '', [0]),
                ('file:'+js, 'reads', 'file:'+notes, 'On export click', [1, 2, 4]),
                ('file:'+js, 'downloads', 'artifact:notes.csv', 'After successful fetch and JSON decoding', [2, 3, 4])])
    if args.slice == 'resume':
        # All mapper processes have exited. Preserve the first decision and its exact owned shard.
        state = Path(run['decisions'])
        old = json.loads(state.read_text())
        old_shard = (Path(run['shards'])/'notes.json').read_bytes()
        times.clear()
        calls.clear()
        start = time.perf_counter()
    if args.slice in ('held', 'resume', 'live'):
        entries = json.loads(Path(run['inventory']).read_text())['entries']
        paths = [e['path'] for e in entries if e['path'].startswith('.github/workflows/')
                 and Path(e['path']).name in SHORTLIST and e['eligible']]
        if len(paths) != len(SHORTLIST):
            raise ValueError('candidate inventory differs')
        candidates = ranked(paths, args.arm == 'C', provider)
        if args.slice == 'live':
            detail = (' Trace the prepublication checks to a concrete script, the revision value to its generated file,'
                      ' artifact packaging, and the verification conditions for each host.')
            plan['questions'].append(dict(id='revision', question=QUESTION+detail, seeds=candidates, depends_on=[]))
            plan_path.write_text(json.dumps(plan), encoding='utf-8')
            prompt = cli('worker-prompt', rid, 'revision')['prompt']
            (repo/'assignment.txt').write_text(prompt, encoding='utf-8')
            print(json.dumps(dict(run=rid, setup_seconds=time.perf_counter()-start, provider=provider,
                                  assignment=str(repo/'assignment.txt'), shard=str(Path(run['shards'])/'revision.json'))))
            return
        for path in candidates:
            probe = cli('read-input', rid, '@', path, '--count', 1)
            if probe['lines'] == ['name: Publish REA website']:
                break
        else:
            raise ValueError('publisher missing from reserve')
        script = 'scripts/website.py'
        investigate('revision', QUESTION, [path], [
            [(path, 67, 2, ['scripts/website.py check']), (path, 69, 12, ['deployment.json', 'GITHUB_SHA']),
             (path, 83, 15, ['website/_site', 'artifact.tar', 'name: github-pages']),
             (path, 140, 7, ['actions/deploy-pages', 'page_url', 'inputs.target']),
             (path, 167, 30, ['GITHUB_SHA', 'pages_url', 'target == "both"', 'deployment.json',
                             'actual == expected', 'if pending:'])],
            [(script, 330, 5, ['"check"', 'prepare-website.py', 'run_script(root, name)'])]], [
                ('file:'+path, 'invokes', 'file:'+script, 'With the check subcommand', [0, 5]),
                ('env:GITHUB_SHA', 'supplies', 'artifact:deployment.json', 'During website preparation', [1]),
                ('artifact:deployment.json', 'included-in', 'artifact:github-pages', 'Packaged from website/_site', [1, 2]),
                ('step:verify-revisions', 'compares', 'artifact:deployment.json',
                 'Pages always and Cloudflare when target is both', [3, 4])])
    plan_fp = cli('check-plan', rid)['fingerprint']
    cli('publish', rid, '--reviewed-english-plan', plan_fp)
    verified = cli('verify')
    with sqlite3.connect(repo/'.project-mapper/graph.sqlite') as db:
        actual = db.execute('SELECT source,type,target FROM relationships').fetchall()
    if sorted(actual) != sorted(expected) or verified['status'] != 'complete':
        raise ValueError('graph differs from frozen relation set')
    if args.slice == 'resume' and (json.loads(state.read_text()).get('notes') != old['notes']
                                    or (Path(run['shards'])/'notes.json').read_bytes() != old_shard):
        raise ValueError('accepted checkpoint changed')
    report = dict(arm=args.arm, slice=args.slice, seconds=time.perf_counter()-start, stages=times, calls=calls,
                  verification=verified, provider=provider, ranges=len(all_pages),
                  evidence_digest=sha256(json.dumps(all_pages, sort_keys=True).encode()).hexdigest())
    (repo/'result.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('source', 'mapper', 'output'):
        parser.add_argument(arg, type=Path)
    parser.add_argument('arm', choices='ABC')
    parser.add_argument('slice', choices=('dev', 'held', 'resume', 'live'))
    run(parser.parse_args())
