"""Reconcile validated extraction across areas and derive graph dimensions."""

from collections import defaultdict
from pathlib import PurePosixPath
import re
import sys

from python_profile import MANIFEST, PROFILE
from scan_files import digest


class Graph:
    def __init__(self, profile=PROFILE):
        self.profile = profile
        self.nodes = {}
        self.relationships = {}
        self.memberships = {}
        self.node_observations = set()
        self.occurrences = {}
        self.observations = {}
        self.provenance = {}
        self.issues = defaultdict(set)
        self.discrepancies = []

    def observe(self, anchor, basis, authority, limitation=''):
        occurrence = digest(anchor)
        self.occurrences[occurrence] = anchor
        provenance = dict(profile=self.profile['name'], version=self.profile['version'], method=basis)
        context = digest(provenance)
        self.provenance[context] = provenance
        data = dict(occurrence=occurrence, context=context, basis=basis, authority=authority,
                    limitation=limitation)
        key = digest(data)
        self.observations[key] = data
        return key

    def node(self, key, kind, namespace, name, observations=(), external=False):
        self.nodes[key] = dict(key=key, kind=kind, namespace=namespace, name=name, external=external)
        self.node_observations.update((key, evidence) for evidence in observations)
        return key

    def relation(self, kind, source, target, state, evidence, *, candidates=(), conditions=(),
                 reason='', discriminator=''):
        family = 'semantic' if kind in self.profile['edge_types']['semantic'] else 'structural'
        data = dict(type=kind, family=family, source=source, target=target, state=state,
                    candidates=sorted(set(candidates)), conditions=list(conditions), reason=reason,
                    discriminator=discriminator)
        key = digest(data)
        item = self.relationships.setdefault(key, dict(data, evidence=set()))
        item['evidence'].update(evidence)

    def member(self, dimension, group, node, evidence):
        self.memberships.setdefault((dimension, group, node), set()).update(evidence)

    def issue(self, path, family, reason):
        self.issues[path, family].add(reason)

    def discrepancy(self, kind, path, reason, evidence):
        self.discrepancies.append(dict(kind=kind, path=path, reason=reason, evidence=sorted(set(evidence))))


def module_layout(path, paths, explicit):
    if explicit is not None:
        if explicit and not path.startswith(explicit + '/'):
            return None, []
        prefix = f'{explicit}/' if explicit else ''
    else:
        prefix = 'src/' if path.startswith('src/') else ''
    relative = path[len(prefix):]
    parts = PurePosixPath(relative).with_suffix('').parts
    is_package = parts[-1] == '__init__'
    package = parts[:-1]
    init_paths = [prefix + '/'.join((*package[:depth], '__init__.py'))
                  for depth in range(1, len(package) + 1)]
    names = package if is_package else parts
    if not names or not all(part.isidentifier() for part in names) or not set(init_paths) <= paths:
        return None, []
    return '.'.join(names), init_paths


def import_base(spec, module, package):
    if not spec['level']:
        return spec['module']
    parts = (module if package else module.rpartition('.')[0]).split('.')
    if parts == [''] or spec['level'] > len(parts):
        return None
    stem = parts[:len(parts) + 1 - spec['level']]
    return '.'.join([*stem, *([spec['module']] if spec['module'] else [])])


def guard_conditions(path, conditions):
    return [dict(condition, path=path) for condition in conditions]


class Reconciler:
    def __init__(self, outcomes):
        self.outcomes = outcomes
        self.graph = Graph()
        self.sources = {}
        self.modules = defaultdict(list)
        self.definitions = defaultdict(list)
        self.imports = defaultdict(list)
        self.manifest = outcomes.get(MANIFEST, {})
        self.config = self.manifest['facts'] if self.manifest.get('kind') == 'manifest' else {}
        self.root = self.config.get('root')

    def index(self):
        graph = self.graph
        python = {path: outcome['facts'] for path, outcome in self.outcomes.items()
                  if outcome['kind'] == 'python'}
        parsed_paths = set(python)
        explicit = self.root['path'] if self.root else None
        layout = {}
        for path, facts in python.items():
            name, parents = module_layout(path, parsed_paths, explicit)
            if name:
                layout[path] = (name, parents)
                self.modules[name].append(path)
            else:
                graph.node(f'file:{path}', 'file', 'repository', path,
                           [graph.observe(facts['module'], 'source-file', 'source')])
                for family in ('structural', 'semantic', 'membership'):
                    graph.issue(path, family, 'file is outside supported package roots or has missing __init__.py')
        context = []
        root_issue = next((risk for risk in self.config.get('risks', []) if 'source root' in risk), '')
        if self.manifest.get('kind') == 'parse':
            root_issue = 'source root configuration could not be parsed'
        if self.root:
            context = [graph.observe(self.root['anchor'], 'setuptools-source-root', 'declaration')]
            if explicit and not any(path.startswith(explicit + '/') for path in python):
                root_issue = 'declared source root has no parsed Python inputs'
                graph.discrepancy('missing-source-root', MANIFEST, root_issue, context)
        if root_issue:
            for family in ('structural', 'semantic', 'membership'):
                graph.issue(MANIFEST, family, root_issue)
        self.layout_issue = root_issue
        for path, (name, parents) in layout.items():
            facts = python[path]
            namespace = f'{name}@{path}' if len(self.modules[name]) > 1 else name
            module_observations = [graph.observe(facts['module'], 'module-source', 'source'), *context]
            self.sources[path] = dict(key=f'module:{namespace}', name=name,
                                      package=path.endswith('/__init__.py'), anchor=module_observations[0],
                                      layout=module_observations)
            if len(self.modules[name]) > 1 or root_issue:
                issue = root_issue or 'multiple source paths for one import name'
                for family in ('structural', 'semantic', 'membership'):
                    graph.issue(path, family, issue)
        for path, (name, parents) in layout.items():
            facts = python[path]
            source = self.sources[path]
            module = source['key']
            graph.node(module, 'module', module.removeprefix('module:'), name, source['layout'])
            package = name.split('.')[0] if parents else '(loose modules)'
            package_evidence = [self.sources[parent]['anchor'] for parent in parents if parent in self.sources]
            graph.member('source-package', package, module, [*source['layout'], *package_evidence])
            if parents and (parent := next((item for item in reversed(parents) if item != path), None)):
                graph.relation('contains', self.sources[parent]['key'], module, 'resolved',
                               [*source['layout'], *package_evidence])
            elif not source['package'] and parents:
                raise AssertionError('module package chain')
            for entry in facts['definitions']:
                name = entry['name']
                key = f'function:{module.removeprefix("module:")}:{name}'
                ev = graph.observe(entry['anchor'], 'function-definition', 'source')
                self.definitions[path, name].append(dict(key=key, evidence=ev, stable=entry['stable']))
                graph.node(key, 'function', module.removeprefix('module:'), name, [ev])
                graph.relation('contains', module, key, 'resolved', [source['anchor'], ev])
                graph.member('source-package', package, key, [*source['layout'], *package_evidence, ev])
            for test_path in self.config.get('tests', []):
                if path.startswith(test_path.rstrip('/') + '/') and (PurePosixPath(path).name.startswith('test_')
                        or path.endswith('_test.py')):
                    test_ev = graph.observe(self.config['test_anchor'], 'pytest-testpaths', 'declaration')
                    graph.member('declared-test-suite', test_path, module, [source['anchor'], test_ev])
            for risk in facts['risks']:
                graph.issue(path, 'semantic', risk)

    def structure(self, path, facts):
        graph = self.graph
        source = self.sources[path]
        for spec in facts['imports']:
            observation = graph.observe(spec['anchor'], 'import-statement', 'declaration')
            base = import_base(spec, source['name'], source['package'])
            member = spec['member']
            child = f'{base}.{member}' if base and member and member != '*' else None
            base_paths = self.modules.get(base, [])
            child_paths = self.modules.get(child, [])
            candidates = list(base_paths)
            mode = 'base'
            if child_paths and len(base_paths) == 1:
                symbol_paths = [p for p in base_paths if member in self.outcomes[p]['facts']['bindings']]
                candidates = [*symbol_paths, *child_paths]
                mode = 'child'
            elif child_paths:
                candidates = [*base_paths, *child_paths]
            # The interpreter's built-in importer runs before filesystem lookup.
            # Other standard-library names may legitimately be provided by the project.
            if not spec['level'] and base and base.split('.')[0] in PROFILE['builtin_modules']:
                candidates = []
            evidence = [source['anchor'], observation]
            target = None
            state = 'unresolved'
            reason = 'import namespace unavailable'
            if self.layout_issue:
                reason = self.layout_issue
            elif len(candidates) == 1:
                candidate = self.sources[candidates[0]]
                target, state, reason = candidate['key'], 'resolved', ''
                evidence.extend(candidate['layout'])
                evidence.extend(source['layout'])
            elif len(candidates) > 1:
                reason = 'multiple module or package attribute candidates'
            elif not spec['level'] and base and base.split('.')[0] in sys.stdlib_module_names:
                top = base.split('.')[0]
                target = graph.node(f'external-module:{top}', 'module', 'python-stdlib', top,
                                    external=True)
                state, reason = 'declared-external', ''
            possible = [self.sources[item]['key'] for item in candidates]
            graph.relation('imports', source['key'], target, state, evidence, candidates=possible if not target else (),
                           conditions=guard_conditions(path, spec['conditions']), reason=reason,
                           discriminator=f'{base or ""}:{member or ""}')
            if state == 'unresolved':
                graph.issue(path, 'structural', reason)
            self.imports[path, spec['binding_scope'], spec['bind']].append(
                dict(spec, base=base, paths=candidates, mode=mode, observation=observation, state=state))

    def binding_targets(self, alias, parts):
        paths = alias['paths']
        name = parts[-1]
        if alias['member'] is not None:
            if len(parts) == 1 and alias['mode'] == 'base':
                return [item for path in paths for item in self.definitions[path, alias['member']]]
            if len(parts) == 2 and alias['mode'] == 'child':
                child = f'{alias["base"]}.{alias["member"]}'
                return [item for path in paths if self.sources[path]['name'] == child
                        for item in self.definitions[path, name]]
            return []
        qualifier = alias['module'].split('.') if alias['plain'] else [alias['bind']]
        if parts[:-1] != qualifier:
            return []
        return [item for path in paths for item in self.definitions[path, name]]

    def semantics(self, path, facts):
        graph = self.graph
        module = self.sources[path]
        for call in facts['calls']:
            caller = self.definitions[path, call['caller']]
            key = caller[0]['key'] if len(caller) == 1 else module['key']
            parts = call['parts']
            aliases = self.imports[path, call['binding_scope'], parts[0]] if parts else []
            possible = [(alias, target) for alias in aliases for target in self.binding_targets(alias, parts)]
            reason = call['reason']
            if not reason and len(caller) != 1:
                reason = 'caller definition ambiguous'
            if not reason and (len(aliases) != 1 or not aliases[0]['stable']):
                reason = 'no unique unconditional global import binding'
            if not reason and aliases[0]['state'] != 'resolved':
                reason = 'import does not resolve to one internal module'
            if not reason and (len(possible) != 1 or not possible[0][1]['stable']):
                reason = 'direct target is unavailable, decorated or rebound'
            observation = graph.observe(call['anchor'], 'call-expression', 'source',
                                        'static binding only' if not reason else reason)
            evidence = [observation, *(entry['evidence'] for entry in caller)]
            evidence.extend(alias['observation'] for alias in aliases)
            evidence.extend(item['evidence'] for _, item in possible)
            target = None
            if not reason:
                alias, candidate = possible[0]
                target = candidate['key']
                evidence.extend(self.sources[alias['paths'][0]]['layout'])
                evidence.extend(module['layout'])
            else:
                graph.issue(path, 'semantic', reason)
            graph.relation('calls', key, target, 'resolved' if target else 'unresolved', evidence,
                           candidates=[item['key'] for _, item in possible] if not target else (),
                           conditions=guard_conditions(path, call['conditions']), reason=reason,
                           discriminator='.'.join(parts) if not target else '')

    def declarations(self):
        graph = self.graph
        if not self.config:
            return
        project = self.config['name'] or '(repository)'
        project_ev = graph.observe(self.config['anchor'], 'project-metadata', 'declaration')
        project_node = graph.node(f'project:{project}', 'project', 'pyproject', project, [project_ev])
        for dep in self.config['dependencies']:
            evidence = graph.observe(dep['anchor'], 'requirement-declaration', 'declaration')
            target = graph.node(f'distribution:{dep["name"]}', 'distribution', 'python-distribution',
                                dep['name'], external=True)
            condition = [dict(kind='requirement-marker', locator=dep['anchor']['symbol'])]
            graph.relation(dep['type'], project_node, target, 'declared-external', [evidence, project_ev],
                           conditions=condition if dep['conditional'] else [])
        for registration in self.config['scripts']:
            evidence = graph.observe(registration['anchor'], 'console-script-declaration', 'declaration',
                                     'declared invocation only')
            node = graph.node(f'entry-point:{project}:{registration["name"]}', 'entry-point', project,
                              registration['name'], [evidence])
            graph.member('declared-entry-point', project, node, [evidence])
            destination = registration['destination']
            name, _, member = (destination or '').partition(':')
            paths = self.modules.get(name, [])
            targets = [item for path in paths for item in self.definitions[path, member]]
            target = None
            if len(paths) == len(targets) == 1 and targets[0]['stable'] and not self.layout_issue:
                target = targets[0]['key']
            findings = [evidence, *[item['evidence'] for item in targets]]
            findings.extend(ev for path in paths for ev in self.sources[path]['layout'])
            if target:
                graph.relation('registers', node, target, 'resolved', findings)
                graph.member('declared-entry-point', project, target, findings)
            else:
                reason = 'declared entry point target has no unique supported definition'
                graph.relation('registers', node, None, 'unresolved', findings,
                               candidates=[item['key'] for item in targets], reason=reason)
                graph.issue(MANIFEST, 'semantic', reason)
                graph.issue(MANIFEST, 'membership', reason)
                graph.discrepancy('unresolved-entry-point', MANIFEST, reason, findings)
        for risk in self.config['risks']:
            graph.issue(MANIFEST, 'structural', risk)

    def run(self):
        self.index()
        for path in self.sources:
            self.structure(path, self.outcomes[path]['facts'])
        for path in self.sources:
            self.semantics(path, self.outcomes[path]['facts'])
        self.declarations()
        for path, outcome in self.outcomes.items():
            if outcome['kind'] == 'signal':
                for anchor in outcome['facts']:
                    evidence = self.graph.observe(anchor, 'architecture-heading', 'candidate',
                                                  'heading warrants inspection of the declaration')
                    self.graph.discrepancy('unexamined-declaration', path,
                                           'architecture claim requires corroboration', [evidence])
        return self.graph


def reconcile(outcomes):
    return Reconciler(dict(sorted(outcomes.items()))).run()
