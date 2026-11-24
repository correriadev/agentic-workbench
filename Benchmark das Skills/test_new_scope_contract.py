"""Exercise the current New Scope CLI without changing a real project."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

cli = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as temporary:
    folder = Path(temporary).resolve() / 'docs' / 'specs' / 'payment'

    def run(operation, *args, payload=None):
        result = subprocess.run([sys.executable, str(cli), str(folder), operation, *args],
                                input=json.dumps(payload) if payload is not None else None,
                                capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    assert run('init')['revision'] == 0
    nodes = [
        dict(id='I1', kind='intent', title='Payment', content='Accept a payment.',
             state='confirmed', origin='human'),
        dict(id='A1', kind='acceptance', title='Result', content='Record one payment.',
             state='planned', origin='inference'),
    ]
    assert run('apply', '--expect', '0', payload=dict(request_id='initial',
               reason='Capture the fixture', nodes=nodes))['revision'] == 1
    run('render-scope')
    assert run('inspect')['scope_current']
    assert run('get', 'A1')['kind'] == 'acceptance'
    projection = run('export-execute-scope')
    assert projection['blueprint_source']['revision'] == 1
    assert projection == run('export-forge')
    print('PASS: specification, scope, source binding and compatible exports')
