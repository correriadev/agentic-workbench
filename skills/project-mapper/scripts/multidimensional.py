"""Conservative snapshot-backed JavaScript and configuration observations.

JS is lexed, not parsed: import-like references are candidates even if their
relative destination resolves. No project code or package manager is run.
"""

import json
import posixpath
import re
import tomllib
from pathlib import PurePosixPath

from extraction_cache import merge_graph, pack_graph
from python_profile import Source
from resolve import Graph
from scan_files import digest


PROFILE = {
    'name': 'multidimensional-static', 'version': 1,
    'languages': ['JavaScript/TypeScript lexical candidates'],
    'formats': ['package.json', 'mcp.json', 'wrangler.toml', 'GitHub Actions run declarations'],
    'edge_types': {'structural': ['imports', 'registers', 'declares-dependency', 'declares-script',
                                  'declares-service', 'configures-entry', 'uses-binding', 'runs-script',
                                  'defines', 'declares-tool', 'uses-config'],
                   'semantic': []},
    'dimensions': ['code', 'test', 'entrypoint', 'dependency', 'configuration', 'infrastructure'],
    'limitations': ['JS/TS is lexed, not parsed; import references are candidates',
                    'calls, route registration, alias resolution and dynamic expressions are not analyzed',
                    'configuration values and command bodies are not recorded'],
}

JS_EXTENSIONS = {'.js', '.mjs', '.cjs', '.jsx', '.ts', '.mts', '.cts', '.tsx'}
SAFE_NAME = re.compile(r'^[A-Za-z0-9_@./:+-]{1,200}$')
IDENTIFIER = re.compile(r'[A-Za-z_$][A-Za-z0-9_$]*')


def tokens(text):
    """Yield conservative JS tokens, ignoring comments, strings as code and templates.

    Regex literals are skipped when they start an expression; templates are
    skipped wholesale because expressions inside them need a real parser.
    """
    result = []
    i = 0
    line = 1
    previous = ''
    expression_prefix = {'', '(', '[', '{', '=', ':', ',', ';', '!', '?', 'return', '=>'}
    while i < len(text):
        c = text[i]
        if c.isspace():
            line += c == '\n'
            i += 1
            continue
        if text.startswith('//', i):
            end = text.find('\n', i + 2)
            i = len(text) if end < 0 else end
            continue
        if text.startswith('/*', i):
            end = text.find('*/', i + 2)
            end = len(text) if end < 0 else end + 2
            line += text[i:end].count('\n')
            i = end
            continue
        if c == '`':
            end = i + 1
            while end < len(text):
                if text[end] == '\\':
                    end += 2
                elif text[end] == '`':
                    end += 1
                    break
                else:
                    end += 1
            line += text[i:end].count('\n')
            i = end
            previous = 'literal'
            continue
        if c in "'\"":
            start = i + 1
            end = start
            escaped = False
            while end < len(text) and text[end] != c and text[end] not in '\r\n':
                if text[end] == '\\':
                    escaped = True
                    end += 2
                else:
                    end += 1
            if end < len(text) and text[end] == c:
                if not escaped:
                    result.append(('string', text[start:end], line))
                i = end + 1
            else:
                i = end
            previous = 'literal'
            continue
        if c == '/' and previous in expression_prefix:
            end = i + 1
            bracket = False
            while end < len(text) and text[end] not in '\r\n':
                if text[end] == '\\':
                    end += 2
                    continue
                if text[end] == '[':
                    bracket = True
                if text[end] == ']':
                    bracket = False
                if text[end] == '/' and not bracket:
                    end += 1
                    while end < len(text) and text[end].isalpha():
                        end += 1
                    break
                end += 1
            i = end
            previous = 'literal'
            continue
        identifier = IDENTIFIER.match(text, i)
        if identifier:
            value = identifier.group()
            result.append(('id', value, line))
            previous = value
            i += len(value)
            continue
        punctuation = next((value for value in ('=>', '?.') if text.startswith(value, i)), c)
        result.append(('punct', punctuation, line))
        previous = punctuation
        i += len(punctuation)
    return result


def import_candidates(text, sequence=None):
    sequence = tokens(text) if sequence is None else sequence
    for index, (kind, word, line) in enumerate(sequence):
        if kind != 'id' or word not in {'import', 'export', 'require'}:
            continue
        if index and sequence[index - 1][1] in {'.', '?.'}:
            continue
        tail = sequence[index + 1:index + 101]
        if not tail:
            continue
        if word in {'import', 'require'} and tail[0][1] == '(':
            if len(tail) >= 3 and tail[1][0] == 'string' and tail[2][1] == ')':
                yield tail[1][1], line, 'dynamic' if word == 'import' else 'require'
        elif word == 'import' and tail[0][0] == 'string':
            yield tail[0][1], line, 'static'
        elif word in {'import', 'export'}:
            for offset, token in enumerate(tail):
                if token[1] == ';' or (token[0] == 'id' and token[1] in {'import', 'export'}):
                    break
                if token[0] == 'id' and token[1] == 'from' and offset + 1 < len(tail):
                    if tail[offset + 1][0] == 'string':
                        yield tail[offset + 1][1], line, 'static'
                    break


def candidate_paths(path, spec):
    if not spec.startswith(('./', '../')) or not SAFE_NAME.fullmatch(spec):
        return []
    base = posixpath.normpath(posixpath.join(posixpath.dirname(path), spec))
    if base.startswith('../') or base == '..' or base.startswith('/'):
        return []
    suffix = PurePosixPath(base).suffix
    stems = [base]
    if suffix in {'.js', '.mjs', '.cjs'}:
        extensions = {'.js': ('.ts', '.tsx'), '.mjs': ('.mts',), '.cjs': ('.cts',)}[suffix]
        stems.extend(base[:-len(suffix)] + ext for ext in extensions)
    if not suffix:
        stems.extend(base + ext for ext in sorted(JS_EXTENSIONS))
        stems.extend(base + '/index' + ext for ext in sorted(JS_EXTENSIONS))
    return sorted(set(stems))


def file_node(graph, path):
    return graph.node('file:' + path, 'file', 'repository', path)


def javascript_candidates(graph, source, sequence):
    """Index explicit lexical candidates without claiming symbol or MCP resolution."""
    path = source.path
    root = 'file:' + path
    # Precompute which balanced object bodies contain a direct `run:` key.
    # Traversing the body anew for every nested candidate is quadratic.
    stack = []
    callable_bodies = set()
    for position, token in enumerate(sequence):
        if token[0] == 'punct' and token[1] == '{':
            stack.append([position, False])
        elif token[0] == 'punct' and token[1] == '}' and stack:
            opening, has_run = stack.pop()
            if has_run:
                callable_bodies.add(opening)
        elif (stack and token[0] == 'id' and token[1] == 'run' and position + 1 < len(sequence)
              and sequence[position + 1][1] == ':'):
            stack[-1][1] = True
    for index, (kind, word, line) in enumerate(sequence):
        if word == 'export' and kind == 'id':
            tail = sequence[index + 1:index + 7]
            while tail and tail[0][1] in {'default', 'async', 'declare'}:
                tail = tail[1:]
            if len(tail) >= 2 and tail[0][1] in {'const', 'let', 'var', 'function', 'class'} and tail[1][0] == 'id':
                name = tail[1][1]
                ev = graph.observe(source.anchor('export-candidate', name, line=line),
                                   'javascript-lexical-export', 'candidate',
                                   'Lexical export candidate; binding and runtime behavior not resolved.')
                node = graph.node('symbol:' + path + ':' + name, 'symbol', path, name, [ev])
                graph.relation('defines', root, node, 'resolved', [ev])
        config_name = re.fullmatch(r'[A-Z][A-Z0-9_]{1,120}', word)
        dot_property = (kind == 'id' and index >= 2 and sequence[index - 1][1] in {'.', '?.'}
                        and sequence[index - 2][1] in {'env', 'environment', 'config'})
        bracket_property = (kind == 'string' and index >= 2 and index + 1 < len(sequence)
                            and sequence[index - 1][1] == '[' and sequence[index + 1][1] == ']'
                            and (sequence[index - 2][1] in {'env', 'environment', 'config'}
                                 or (index >= 3 and sequence[index - 2][1] == '?.'
                                     and sequence[index - 3][1] in {'env', 'environment', 'config'})))
        if config_name and (dot_property or bracket_property):
            ev = graph.observe(source.anchor('configuration-candidate', word, line=line),
                               'javascript-lexical-config', 'candidate',
                               'Property name candidate; source and effective configuration are not resolved.')
            node = graph.node('config:' + word, 'configuration', 'environment-candidate', word, [ev])
            graph.relation('uses-config', root, node, 'resolved', [ev])
            graph.member('configuration', 'candidate', node, [ev])
        if (kind == 'id'
                and re.fullmatch(r'[a-z][a-z0-9]*(?:_[a-z0-9]+)+', word)
                and index + 2 < len(sequence) and sequence[index + 1][1] == ':'
                and index + 2 in callable_bodies):
            ev = graph.observe(source.anchor('callable-object-candidate', word, line=line),
                               'javascript-lexical-callable', 'candidate',
                               'Callable object key candidate; framework, registration and handler require verification.')
            node = graph.node('tool-candidate:' + path + ':' + word, 'tool-candidate', path, word, [ev])
            graph.relation('declares-tool', root, node, 'resolved', [ev])
            graph.member('entrypoint', 'callable-object-candidate', node, [ev])


def link_file(graph, relation, source, targets, evidence, reason):
    if len(targets) == 1:
        graph.relation(relation, source, 'file:' + targets[0], 'resolved', [evidence])
    else:
        graph.relation(relation, source, None, 'unresolved', [evidence],
                       candidates=['file:' + target for target in targets], reason=reason)


def json_anchor(source, key):
    anchor = source.toml_anchor(key)
    anchor['kind'] = 'json-key'
    return anchor


def local_path(path, value, paths):
    if not isinstance(value, str) or not SAFE_NAME.fullmatch(value):
        return []
    result = posixpath.normpath(posixpath.join(posixpath.dirname(path), value))
    return [result] if result in paths else []


def extract_package(graph, source, paths):
    data = json.loads(source.text)
    if not isinstance(data, dict):
        raise ValueError('package must be an object')
    root = 'file:' + source.path
    for section in ('dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies'):
        values = data.get(section, {})
        if not isinstance(values, dict):
            continue
        for name in sorted(values):
            if not SAFE_NAME.fullmatch(name):
                continue
            ev = graph.observe(json_anchor(source, section + '.' + name), 'json-dependency', 'declaration')
            key = graph.node('dependency:' + name, 'dependency', 'npm', name, [ev], external=True)
            graph.relation('declares-dependency', root, key, 'declared-external', [ev],
                           discriminator=section)
            graph.member('dependency', section, key, [ev])
    scripts = data.get('scripts', {})
    if isinstance(scripts, dict):
        for name in sorted(scripts):
            if not SAFE_NAME.fullmatch(name):
                continue
            ev = graph.observe(json_anchor(source, 'scripts.' + name), 'json-script', 'declaration',
                               'Command body is deliberately omitted.')
            key = graph.node('npm-script:' + source.path + ':' + name, 'command', 'npm', name, [ev])
            graph.relation('declares-script', root, key, 'resolved', [ev])
    bins = data.get('bin', {})
    if isinstance(bins, str):
        bins = {data.get('name', ''): bins}
    if isinstance(bins, dict):
        for name, value in sorted(bins.items()):
            if not isinstance(name, str) or not SAFE_NAME.fullmatch(name):
                continue
            ev = graph.observe(json_anchor(source, 'bin.' + name), 'json-bin', 'declaration')
            key = graph.node('command:' + source.path + ':' + name, 'command', 'npm-bin', name, [ev])
            graph.member('entrypoint', 'cli', key, [ev])
            graph.relation('registers', root, key, 'resolved', [ev])
            link_file(graph, 'registers', key, local_path(source.path, value, paths), ev,
                      'Declared entry point does not resolve to one eligible file.')


def extract_mcp(graph, source):
    data = json.loads(source.text)
    if not isinstance(data, dict):
        raise ValueError('mcp configuration must be an object')
    servers = data.get('mcpServers', {})
    if not isinstance(servers, dict):
        raise ValueError('mcpServers must be an object')
    for name in sorted(servers):
        if not SAFE_NAME.fullmatch(name):
            continue
        ev = graph.observe(json_anchor(source, 'mcpServers.' + name), 'mcp-config', 'declaration',
                           'Server command, arguments and environment are not persisted.')
        node = graph.node('mcp-server:' + source.path + ':' + name, 'mcp-server', 'configuration', name, [ev])
        graph.relation('declares-service', 'file:' + source.path, node, 'resolved', [ev])
        graph.member('configuration', 'mcp-server', node, [ev])


def extract_wrangler(graph, source, paths):
    data = tomllib.loads(source.text)
    ev = graph.observe(source.toml_anchor('main'), 'wrangler-main', 'declaration')
    if 'main' in data:
        link_file(graph, 'configures-entry', 'file:' + source.path,
                  local_path(source.path, data['main'], paths), ev,
                  'Declared Worker entry does not resolve to one eligible file.')
    assets = data.get('assets', {})
    binding = assets.get('binding') if isinstance(assets, dict) else None
    if isinstance(binding, str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,100}', binding):
        ev = graph.observe(source.toml_anchor('assets.binding'), 'wrangler-binding', 'declaration')
        node = graph.node('binding:' + source.path + ':' + binding, 'binding', 'wrangler', binding, [ev])
        graph.relation('uses-binding', 'file:' + source.path, node, 'resolved', [ev])
        graph.member('infrastructure', 'worker-binding', node, [ev])


def extract_workflow(graph, source, paths):
    package = 'package.json'
    if package not in paths:
        return
    for line, text in enumerate(source.text.splitlines(), 1):
        match = re.match(r'^\s*run:\s*(?:npm|npx)\s+run\s+([A-Za-z0-9_:+.-]+)\s*$', text)
        if not match:
            continue
        name = match.group(1)
        key = 'npm-script:' + package + ':' + name
        ev = graph.observe(source.anchor('workflow-run', name, line=line), 'yaml-run-line', 'candidate',
                           'Line-based YAML candidate; job conditions and multiline commands are not resolved.')
        if key in graph.nodes:
            graph.relation('runs-script', 'file:' + source.path, key, 'resolved', [ev])


def extract_source_facts(reader, path, profile, csharp_parser):
    graph = Graph(profile)
    relative_imports = []
    project_anchor = None
    try:
        source = Source(reader, path)
        anchor = source.anchor('source-file', path)
        ev = graph.observe(anchor, 'file-inventory', 'source')
        root = graph.node('file:' + path, 'file', 'repository', path, [ev])
        if csharp_parser is not None:
            from csharp_profile import extract
            project_anchor = dict(anchor, kind='dotnet-project-candidate')
            graph.member('code', 'csharp', root, [ev])
            reason = extract(graph, source, csharp_parser)
        else:
            parts = PurePosixPath(path).parts
            is_test = bool(re.search(r'\.(?:test|spec)\.[cm]?[jt]sx?$', parts[-1])) or bool(
                {'tests', '__tests__'}.intersection(parts))
            graph.member('test' if is_test else 'code', 'source', root, [ev])
            sequence = tokens(source.text)
            javascript_candidates(graph, source, sequence)
            for spec, line, method in import_candidates(source.text, sequence):
                if not SAFE_NAME.fullmatch(spec):
                    continue
                anchor = source.anchor('import-candidate', method, line=line)
                evidence = graph.observe(anchor, 'javascript-lexical-import', 'candidate',
                                         'Lexical candidate, not a parsed or runtime-verified import.')
                if spec.startswith(('./', '../')):
                    # The cache only needs to match names in the next inventory.
                    relative_imports.append(([digest(name) for name in candidate_paths(path, spec)], evidence))
                else:
                    key = graph.node('dependency:' + spec, 'dependency', 'npm', spec, [evidence], external=True)
                    graph.relation('imports', root, None, 'unresolved', [evidence], candidates=[key],
                                   reason='Bare reference may be a package or a configured local alias.')
            reason = 'JS/TS imports are lexical candidates; symbols, calls and dynamic dispatch are not analyzed.'
    except (UnicodeError, ValueError, RecursionError) as error:
        reason = f'{type(error).__name__} while parsing supported input.'
    return dict(graph=pack_graph(graph), relative_imports=relative_imports, project_anchor=project_anchor,
                reason=reason)


def extract_graph(manifest, reader, *, csharp=False, profile=None, cache=None):
    graph = Graph(profile or PROFILE)
    csharp_parser = None
    if csharp:
        from csharp_profile import parser
        csharp_parser = parser()
    coverage = []
    outcomes = {}
    entries = manifest['entries']
    paths = {item['path'] for item in entries if item['eligible']}
    path_ids = {digest(path): path for path in paths}
    for path in sorted(paths):
        file_node(graph, path)
    # Resolve workflows after all manifests are processed, regardless of path order.
    workflows = []
    project_anchors = {}
    for item in entries:
        path = item['path']
        if not item['eligible']:
            # Boundaries are inventory facts, not readable source occurrences. Keep
            # them searchable without inventing source evidence or traversing them.
            kind = item['kind']
            if kind in {'submodule', 'boundary', 'symlink', 'pruned-directory'}:
                graph.node('boundary:' + path, kind, 'inventory', path)
            status = item.get('status', 'unsupported')
            reason = item.get('reason') or f'{kind} is outside the eligible snapshot.'
            coverage.append(dict(area=path, family='multidimensional-static', status=status, reason=reason,
                                 task=None, paths=[path], method=['snapshot-inventory'],
                                 basis='ineligible inventory entry', scoped_absence=False,
                                 findings=0, issues=[] if status == 'excluded' else [reason]))
            continue
        suffix = PurePosixPath(path).suffix.lower()
        name = PurePosixPath(path).name
        target = suffix in JS_EXTENSIONS or name in {'package.json', 'mcp.json', 'wrangler.toml'}
        target = target or (path.startswith('.github/workflows/') and suffix in {'.yml', '.yaml'})
        target = target or (csharp and suffix in {'.cs', '.csproj'})
        if not target:
            reason = 'No multidimensional extractor for this input.'
            outcomes[path] = dict(status='unsupported', reason=reason)
            coverage.append(dict(area=path, family='multidimensional-static', status='unsupported', reason=reason,
                                 task=None, paths=[path], method=['snapshot-static'], basis='unsupported input',
                                 scoped_absence=False, findings=0, issues=[reason]))
            continue
        if suffix in JS_EXTENSIONS or csharp and suffix == '.cs':
            parser_for_file = csharp_parser if suffix == '.cs' else None
            if cache is None:
                facts = extract_source_facts(reader, path, graph.profile, parser_for_file)
            else:
                facts = cache.extract(path, item['content_id'], 'csharp' if parser_for_file else 'javascript',
                                      lambda: extract_source_facts(reader, path, graph.profile, parser_for_file))
            merge_graph(graph, facts['graph'])
            for candidates, evidence in facts['relative_imports']:
                targets = sorted(path_ids[key] for key in candidates if key in path_ids)
                link_file(graph, 'imports', 'file:' + path, targets, evidence,
                          'Relative reference is missing or has multiple eligible targets.')
            if facts['project_anchor']:
                project_anchors[path] = facts['project_anchor']
            reason = facts['reason']
        else:
            if cache is not None:
                cache.extracted.add(path)
            try:
                source = Source(reader, path)
                ev = graph.observe(source.anchor('source-file', path), 'file-inventory', 'source')
                graph.node('file:' + path, 'file', 'repository', path, [ev])
                if csharp and suffix == '.csproj':
                    from csharp_profile import extract_project
                    reason = extract_project(graph, source, paths)
                elif name == 'package.json':
                    extract_package(graph, source, paths)
                    reason = 'Package declarations indexed; command bodies and dependency versions are omitted.'
                elif name == 'mcp.json':
                    extract_mcp(graph, source)
                    reason = 'Server identities indexed; commands, arguments and environment are omitted.'
                elif name == 'wrangler.toml':
                    extract_wrangler(graph, source, paths)
                    reason = 'Worker entry and binding declarations indexed; deployment/runtime state is not analyzed.'
                else:
                    workflows.append(source)
                    reason = 'Only simple npm run lines are recognized; YAML conditions and multiline steps are not parsed.'
            except (UnicodeError, ValueError, tomllib.TOMLDecodeError, RecursionError) as error:
                reason = f'{type(error).__name__} while parsing supported input.'
        status = 'partial'
        outcomes[path] = dict(status=status, reason=reason)
        coverage.append(dict(area=path, family='multidimensional-static', status=status, reason=reason,
                             task=None, paths=[path], method=['snapshot-static'], basis='supported input subset',
                             scoped_absence=False, findings=0, issues=[reason]))
    for source in workflows:
        extract_workflow(graph, source, paths)
    if csharp:
        projects = sorted(path for path in paths if path.lower().endswith('.csproj') and
                          'dotnet-project:' + path in graph.nodes)
        for path, anchor in sorted(project_anchors.items()):
            parents = [p for p in projects if str(PurePosixPath(p).parent) == '.' or
                       path.startswith(str(PurePosixPath(p).parent) + '/')]
            if not parents:
                continue
            depth = max(len(PurePosixPath(p).parent.parts) for p in parents)
            nearest = [p for p in parents if len(PurePosixPath(p).parent.parts) == depth]
            ev = graph.observe(anchor, 'dotnet-project-layout', 'candidate',
                               'Directory-based candidate; MSBuild compile inclusion is not evaluated.')
            graph.relation('belongs-to-project', 'file:' + path, None, 'unresolved', [ev],
                           candidates=['dotnet-project:' + p for p in nearest],
                           reason='Project inclusion and imported MSBuild properties are not evaluated.')
    # Count distinct relations anchored to each file, not raw nodes or observations.
    observation_paths = {key: graph.occurrences[value['occurrence']]['path']
                         for key, value in graph.observations.items()}
    per_path = {}
    for key, value in graph.relationships.items():
        for observation in value['evidence']:
            per_path.setdefault(observation_paths[observation], set()).add(key)
    for row in coverage:
        row['findings'] = len(per_path.get(row['area'], ()))
        row['basis'] += '; findings count distinct source-anchored relations'
    return graph, coverage, outcomes, {}
