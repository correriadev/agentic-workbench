"""Frozen Python profile. Extraction emits candidates; reconciliation binds them."""

import ast
from collections import defaultdict
import hashlib
import io
from pathlib import PurePosixPath
import re
import symtable
import sys
import tokenize
import tomllib

from scan_files import MappingError, digest


PROFILE = {
    'name': 'python-static', 'version': 2, 'parser': f'CPython {sys.version_info.major}.{sys.version_info.minor}',
    'builtin_modules': sorted(sys.builtin_module_names),
    'languages': ['Python'], 'formats': ['pyproject.toml', 'architecture/deployment/contract path signals'],
    'layouts': ['flat regular packages and loose modules', 'conventional src layout',
                'setuptools package-dir empty-key source root'],
    'constructs': ['imports and from imports, including aliases and relative imports',
                   'direct global alias calls inside module-level functions',
                   'top-level function definitions', 'project.scripts console entry points',
                   'project.dependencies, build-system.requires', 'pytest testpaths'],
    'resolution': ['explicit root overrides convention', 'require __init__.py through package chain',
                   'unique module and binding', 'local shadowing via symtable',
                   'no inferred re-exports, conditional alias bindings, decorated targets or dynamic dispatch'],
    'edge_types': {'structural': ['contains', 'imports', 'declares-dependency', 'build-requires'],
                   'semantic': ['calls', 'registers']},
    'dimensions': ['source-package', 'declared-entry-point', 'declared-test-suite'],
}

SUPPORTED = ('structural', 'semantic', 'membership')
MANIFEST = 'pyproject.toml'
DEFINITION = (ast.FunctionDef, ast.AsyncFunctionDef)
SCOPE = DEFINITION + (ast.ClassDef, ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
GUARDS = (ast.If, ast.Try, ast.TryStar, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Match,
          ast.IfExp, ast.BoolOp)
IDENT = r'[A-Za-z_][A-Za-z_0-9]*'
MODULE = rf'{IDENT}(?:\.{IDENT})*'


def signal(path):
    name = PurePosixPath(path).name.lower()
    text = path.lower()
    result = []
    if name.startswith(('dockerfile', 'compose.', 'docker-compose.', 'procfile')) or text.startswith(
            ('.github/workflows/', 'deploy/', 'k8s/', 'helm/')):
        result.append('runtime-deployment')
    if 'asyncapi' in name or name.endswith('.avsc'):
        result.append('event-contract')
    if 'openapi' in name or name.endswith(('.proto', '.graphql', '.wsdl')):
        result.append('interfaces')
    if name.endswith('.sql') or {'migration', 'migrations', 'models'}.intersection(text.split('/')):
        result.append('data-ownership')
    if name.startswith('test_') or 'tests' in text.split('/') or name in {'pytest.ini', 'tox.ini'}:
        result.append('verification')
    if name in {'readme.md', 'architecture.md', 'architecture.rst', 'setup.cfg', 'setup.py'}:
        result.append('architecture-declaration')
    if PurePosixPath(path).suffix.lower() in {
        '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.cs', '.cpp', '.c', '.rb', '.php',
        '.sh', '.ps1', '.pyi', '.ipynb', '.kt', '.swift',
    }:
        result.append('other-language')
    return result


def families(entry):
    path = entry['path']
    if entry['kind'] in {'submodule', 'boundary', 'symlink', 'pruned-directory'}:
        return sorted(set(SUPPORTED) | set(signal(path)))
    if not entry['eligible']:
        return list(SUPPORTED) if path.endswith('.py') or path == MANIFEST else signal(path)
    if path.endswith('.py') or path == MANIFEST:
        return sorted(set(SUPPORTED) | set(signal(path)))
    return signal(path)


def source_text(data, path):
    if path.endswith('.py'):
        encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
        return data.decode(encoding)
    return data.decode('utf-8')


class Source:
    def __init__(self, reader, path):
        self.path = path
        self.content_id = reader.entries[path]['content_id']
        self.text = source_text(reader.read(path), path).replace('\r\n', '\n').replace('\r', '\n')
        self.lines = [line.encode('utf-8') for line in self.text.split('\n')]

    def excerpt(self, span):
        line, col, end, end_col = span
        if not (1 <= line <= end <= len(self.lines) and 0 <= col <= len(self.lines[line - 1])
                and 0 <= end_col <= len(self.lines[end - 1]) and (line < end or col <= end_col)):
            raise MappingError(f'invalid locator span for {self.path}')
        if line == end:
            return self.lines[line - 1][col:end_col]
        return b'\n'.join([self.lines[line - 1][col:], *self.lines[line:end - 1],
                           self.lines[end - 1][:end_col]])

    def anchor(self, kind, symbol='', *, node=None, line=1):
        span = (line, 0, line, len(self.lines[line - 1]))
        if node is not None:
            span = (node.lineno, node.col_offset, node.end_lineno, node.end_col_offset)
        return dict(path=self.path, content_id=self.content_id, span=list(span), kind=kind,
                    symbol=symbol, excerpt_digest=hashlib.sha256(self.excerpt(span)).hexdigest())

    def toml_anchor(self, key):
        # Retain the validated document as locator context. The qualified key selects the
        # claim even when TOML uses dotted keys, quoted names or multiline values.
        span = [1, 0, len(self.lines), len(self.lines[-1])]
        return dict(path=self.path, content_id=self.content_id, span=span, kind='toml-key', symbol=key,
                    excerpt_digest=hashlib.sha256(self.excerpt(span)).hexdigest())


def spelling(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        return [node.id, *reversed(parts)]
    return []


def imports(node):
    for alias in node.names:
        if isinstance(node, ast.Import):
            yield dict(module=alias.name, member=None, level=0, bind=alias.asname or alias.name.split('.')[0],
                       plain=alias.asname is None)
        else:
            yield dict(module=node.module or '', member=alias.name, level=node.level,
                       bind=alias.asname or alias.name, plain=False)


class Bindings(ast.NodeVisitor):
    """Collect all syntactic writes in module scope, with no flow assumptions."""

    def __init__(self):
        self.writes = defaultdict(list)

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.writes[node.id].append(node)

    def visit_Attribute(self, node):
        parts = spelling(node)
        if isinstance(node.ctx, (ast.Store, ast.Del)) and parts:
            self.writes[parts[0]].append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.writes[node.name].append(node)
        for expression in [*node.decorator_list, *node.args.defaults, *node.args.kw_defaults]:
            if expression is not None:
                self.visit(expression)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.writes[node.name].append(node)

    def visit_Lambda(self, node):
        pass

    def visit_comprehension_scope(self, node):
        for child in ast.walk(node):
            if isinstance(child, ast.NamedExpr):
                self.visit(child.target)

    visit_ListComp = visit_SetComp = visit_DictComp = visit_GeneratorExp = visit_comprehension_scope

    def visit_Import(self, node):
        for spec in imports(node):
            self.writes[spec['bind']].append(node)

    visit_ImportFrom = visit_Import

    def capture_name(self, node):
        name = getattr(node, 'name', None) or getattr(node, 'rest', None)
        if name:
            self.writes[name].append(node)
        self.generic_visit(node)

    visit_ExceptHandler = visit_MatchAs = visit_MatchStar = visit_MatchMapping = capture_name


def python_facts(source):
    tree = ast.parse(source.text, filename=source.path)
    symbols = symtable.symtable(source.text, source.path, 'exec')
    bindings = Bindings()
    bindings.visit(tree)
    facts = dict(module=source.anchor('module'), definitions=[], imports=[], calls=[], risks=[])
    facts['bindings'] = sorted(bindings.writes)
    direct = set(tree.body)
    global_declarations = {name for node in ast.walk(tree) if isinstance(node, ast.Global) for name in node.names}
    attribute_writes = {parts[0] for node in ast.walk(tree) if isinstance(node, ast.Attribute)
                        and isinstance(node.ctx, (ast.Store, ast.Del)) and (parts := spelling(node))}
    unique = {name: nodes[0] for name, nodes in bindings.writes.items()
              if len(nodes) == 1 and nodes[0] in direct and name not in global_declarations | attribute_writes}
    for node in tree.body:
        if isinstance(node, DEFINITION):
            facts['definitions'].append(dict(name=node.name, stable=unique.get(node.name) is node
                                             and not node.decorator_list,
                                             anchor=source.anchor('definition', node.name, node=node)))
    scopes = {(child.get_name(), child.get_lineno()): child for child in symbols.get_children()}
    dynamic_names = {'exec', 'eval', 'globals', 'locals', 'setattr', 'delattr', '__import__'}
    dynamic = bool(bindings.writes.get('*')) or any(
        isinstance(node, ast.Call) and spelling(node.func) and spelling(node.func)[-1] in dynamic_names
        for node in ast.walk(tree))

    def visit(node, scope=None, guards=()):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for spec in imports(node):
                module_binding = node in bindings.writes.get(spec['bind'], ())
                # None denotes module scope; zero denotes an unsupported nested scope.
                binding_scope = None if module_binding else (scope.lineno if scope else 0)
                spec.update(anchor=source.anchor('import', spec['bind'], node=node), conditions=list(guards),
                            binding_scope=binding_scope,
                            stable=unique.get(spec['bind']) is node and not dynamic)
                facts['imports'].append(spec)
        if isinstance(node, ast.Call):
            parts = spelling(node.func)
            reason = 'call outside supported function scope'
            binding_scope = None
            if scope and parts:
                table = scopes.get((scope.name, scope.lineno))
                try:
                    symbol = table.lookup(parts[0]) if table else None
                except KeyError:
                    symbol = None
                if symbol and symbol.is_local() and symbol.is_imported():
                    binding_scope = scope.lineno
                reason = '' if symbol and symbol.is_global() and not dynamic else 'shadowed or mutable binding'
            elif scope:
                reason = 'dynamic call expression'
            facts['calls'].append(dict(caller=scope.name if scope else None, parts=parts, reason=reason,
                                       binding_scope=binding_scope,
                                       conditions=list(guards),
                                       anchor=source.anchor('call', '.'.join(parts), node=node)))
        if isinstance(node, SCOPE):
            if node in direct and isinstance(node, DEFINITION):
                body = set(node.body)
                for child in ast.iter_child_nodes(node):
                    visit(child, node if child in body else None, guards)
            else:
                for child in ast.iter_child_nodes(node):
                    visit(child, None, (*guards, dict(kind='nested-scope', line=node.lineno, arm='body')))
            return
        for field, value in ast.iter_fields(node):
            children = value if isinstance(value, list) else [value]
            for child in children:
                if isinstance(child, ast.AST):
                    child_guards = guards
                    if isinstance(node, GUARDS):
                        child_guards = (*guards, dict(kind=type(node).__name__, line=node.lineno, arm=field))
                    visit(child, scope, child_guards)

    visit(tree)
    if dynamic:
        facts['risks'].append('dynamic namespace changes or wildcard binding')
        for definition in facts['definitions']:
            definition['stable'] = False
    return facts


def section(data, *keys):
    for key in keys:
        data = data.get(key, {}) if isinstance(data, dict) else {}
    return data


def manifest_facts(source):
    data = tomllib.loads(source.text)
    project = section(data, 'project')
    name = section(project, 'name')
    name = name if isinstance(name, str) and re.fullmatch(r'[\w.-]+', name) else None
    package_dir = section(data, 'tool', 'setuptools', 'package-dir')
    root = None
    risks = []
    if package_dir:
        if isinstance(package_dir, dict) and set(package_dir) == {''} and isinstance(package_dir[''], str):
            raw = package_dir['']
            parts = raw.split('/')
            if raw in {'', '.'} or all(re.fullmatch(r'[\w.-]+', p) and p not in {'.', '..'} for p in parts):
                root = dict(path='' if raw in {'', '.'} else raw, anchor=source.toml_anchor(
                    'tool.setuptools.package-dir[""]'))
            else:
                risks.append('unsupported source root path')
        else:
            risks.append('unsupported source root mapping')
    scripts = []
    declaration = section(project, 'scripts')
    if isinstance(declaration, dict):
        for script, value in sorted(declaration.items()):
            supported = isinstance(value, str) and re.fullmatch(rf'{MODULE}:{IDENT}', value)
            safe_name = script if re.fullmatch(r'[\w.-]+', script) else f'key-{digest(script)[:16]}'
            scripts.append(dict(name=safe_name, destination=value if supported else None,
                                anchor=source.toml_anchor(f'project.scripts.{safe_name}')))
    else:
        risks.append('unsupported project.scripts declaration')
    dependencies = []
    dynamic = section(project, 'dynamic')
    if isinstance(dynamic, list) and 'dependencies' in dynamic:
        risks.append('project.dynamic delegates dependencies to the build backend; inspect its configuration')
    for keys, kind in [(('project', 'dependencies'), 'declares-dependency'),
                       (('build-system', 'requires'), 'build-requires')]:
        values = section(data, *keys)
        if isinstance(values, list):
            for index, value in enumerate(values):
                match = re.match(r'^([A-Za-z0-9][A-Za-z0-9._-]*)(?=[\s\[<>=!~;@]|$)', value) if isinstance(value, str) else None
                if not match:
                    risks.append('unsupported requirement declaration')
                    continue
                dependencies.append(dict(name=re.sub(r'[-_.]+', '-', match[1]).lower(), type=kind,
                                         conditional=';' in value,
                                         anchor=source.toml_anchor(f'{".".join(keys)}[{index}]')))
        elif values:
            risks.append('unsupported requirement declaration')
    declared_tests = section(data, 'tool', 'pytest', 'ini_options', 'testpaths')
    tests = [value for value in declared_tests if isinstance(value, str) and
             re.fullmatch(r'[\w/-]+', value) and not value.startswith('/')] if isinstance(declared_tests, list) else []
    if declared_tests and len(tests) != len(declared_tests):
        risks.append('unsupported pytest testpaths')
    return dict(name=name, scripts=scripts, root=root, risks=risks, dependencies=dependencies, tests=tests,
                anchor=source.toml_anchor('project'),
                test_anchor=source.toml_anchor('tool.pytest.ini_options.testpaths'))


def extract(reader, path):
    # Snapshot failures propagate to the supervisor. Unsupported language input is an outcome.
    try:
        source = Source(reader, path)
        if path.endswith('.py'):
            return dict(status='analyzed', kind='python', facts=python_facts(source))
        if path == MANIFEST:
            return dict(status='analyzed', kind='manifest', facts=manifest_facts(source))
        matches = []
        if 'architecture-declaration' in signal(path):
            tokens = re.compile(r'^\s*#{1,6}\s+.*\b(architecture|deployment|runtime|components)\b', re.I)
            matches = [source.anchor('architecture-heading', match[1].lower(), line=index)
                       for index, line in enumerate(source.text.split('\n'), 1) if (match := tokens.search(line))]
        return dict(status='unsupported', kind='signal', facts=matches, reason='outside active extractor profile')
    except (SyntaxError, UnicodeError, LookupError, tomllib.TOMLDecodeError, RecursionError) as error:
        return dict(status='partial', kind='parse', reason=f'{type(error).__name__} in supported input', facts=[])
