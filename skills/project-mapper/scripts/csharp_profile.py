"""Optional syntax-only C# and .NET project extraction; never loads target code."""
import posixpath
import re
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath

from scan_files import MappingError

PROFILE = {'name': 'csharp-syntax', 'version': 1, 'tree_sitter': '0.25.2',
           'grammar': 'tree-sitter-c-sharp==0.23.1'}
SAFE = re.compile(r'^[A-Za-z_][A-Za-z0-9_.`<>?,\[\]]{0,199}$')
ROUTE = re.compile(r'^[A-Za-z0-9_./{}:\[\]-]{1,200}$')
CONFIG = re.compile(r'^[A-Za-z_][A-Za-z0-9_.:-]{0,199}$')
TYPE_DECL = {'class_declaration': 'class', 'interface_declaration': 'interface',
             'struct_declaration': 'struct', 'record_declaration': 'record', 'enum_declaration': 'enum'}
METHOD_DECL = {'method_declaration', 'constructor_declaration'}
HTTP = {'HttpGet', 'HttpPost', 'HttpPut', 'HttpPatch', 'HttpDelete', 'HttpHead', 'HttpOptions'}
TESTS = {'Fact', 'Theory', 'Test', 'TestCase', 'TestMethod', 'DataTestMethod'}


def parser():
    try:
        from importlib.metadata import version
        from tree_sitter import Language, Parser
        import tree_sitter_c_sharp
        if version('tree-sitter') != PROFILE['tree_sitter'] or version('tree-sitter-c-sharp') != '0.23.1':
            raise MappingError('C# extraction requires tree-sitter==0.25.2 and tree-sitter-c-sharp==0.23.1')
        return Parser(Language(tree_sitter_c_sharp.language()))
    except (ImportError, ModuleNotFoundError) as exc:
        raise MappingError('C# extraction requires tree-sitter==0.25.2 and tree-sitter-c-sharp==0.23.1') from exc


def extract(graph, source, syntax_parser):
    raw = source.text.encode('utf-8')
    tree = syntax_parser.parse(raw)
    path = source.path
    file_key = 'file:' + path

    def text(node):
        return raw[node.start_byte:node.end_byte].decode('utf-8') if node else ''

    def observation(node, kind, symbol='', authority='source'):
        return graph.observe(source.anchor(kind, symbol, line=node.start_point.row + 1),
                             'csharp-tree-sitter', authority,
                             'Syntactic observation; bindings and runtime behavior are not established.')

    def literal_argument(node):
        args = next((c for c in node.named_children if c.type in {'attribute_argument_list', 'argument_list'}), None)
        if not args or not args.named_children:
            return ''
        arg = args.named_children[0]
        literal = next((c for c in arg.named_children if c.type == 'string_literal'), None)
        if not literal or any(c.type != 'string_literal_content' for c in literal.named_children):
            return ''
        content = text(literal)[1:-1]
        return content if ROUTE.fullmatch(content) else ''

    root = tree.root_node
    file_ns = next((text(n.child_by_field_name('name')) for n in root.named_children
                    if n.type == 'file_scoped_namespace_declaration'), '')

    def visit(node, namespace, parent_key, owner=''):
        if node.type == 'namespace_declaration':
            name = text(node.child_by_field_name('name'))
            namespace = '.'.join(x for x in (namespace, name) if x)
        if node.type in TYPE_DECL:
            name = text(node.child_by_field_name('name'))
            if name and SAFE.fullmatch(name):
                qualified = '.'.join(x for x in (owner or namespace, name) if x)
                key = f'csharp-type:{path}:{qualified}:{node.start_point.row + 1}'
                ev = observation(node.child_by_field_name('name'), 'csharp-type', name)
                graph.node(key, TYPE_DECL[node.type], 'csharp', name, [ev])
                graph.relation('contains', parent_key, key, 'resolved', [ev])
                for attr_list in (c for c in node.named_children if c.type == 'attribute_list'):
                    for attr in (c for c in attr_list.named_children if c.type == 'attribute'):
                        attr_name = text(attr.child_by_field_name('name')).split('.')[-1].removesuffix('Attribute')
                        if attr_name == 'Route':
                            route = literal_argument(attr)
                            ae = observation(attr, 'controller-route', attr_name, 'candidate')
                            endpoint = graph.node(f'csharp-endpoint:{path}:{node.start_point.row + 1}:Route', 'endpoint', 'controller-route-candidate', f'Route {route}'.strip(), [ae])
                            graph.relation('declares-endpoint', key, endpoint, 'resolved', [ae])
                bases = next((c for c in node.named_children if c.type == 'base_list'), None)
                if bases:
                    for base in bases.named_children:
                        base_name = text(base)
                        if SAFE.fullmatch(base_name):
                            be = observation(base, 'base-type', base_name, 'candidate')
                            ref = graph.node(f'csharp-reference:{path}:{base_name}', 'type-reference', 'csharp', base_name, [be])
                            graph.relation('inherits-or-implements', key, None, 'unresolved', [be], candidates=[ref], reason='Base type binding is not resolved.')
                parent_key, owner = key, qualified
        if node.type in METHOD_DECL:
            name_node = node.child_by_field_name('name')
            name = text(name_node)
            if name and SAFE.fullmatch(name):
                # Source coordinates distinguish overloads and partial declarations.
                key = f'csharp-method:{path}:{owner}:{name}:{node.start_point.row + 1}:{node.start_point.column}'
                ev = observation(name_node, 'csharp-method', name)
                graph.node(key, 'method', 'csharp', name, [ev])
                graph.relation('contains', parent_key, key, 'resolved', [ev])
                parent_key = key
                if node.type == 'constructor_declaration':
                    params = node.child_by_field_name('parameters')
                    if params:
                        for param in (c for c in params.named_children if c.type == 'parameter'):
                            type_node = param.child_by_field_name('type')
                            type_name = text(type_node)
                            if SAFE.fullmatch(type_name):
                                e = observation(type_node, 'constructor-parameter', type_name, 'candidate')
                                target = graph.node(f'csharp-reference:{path}:{type_name}', 'type-reference', 'csharp', type_name, [e])
                                graph.relation('depends-on', key, None, 'unresolved', [e], candidates=[target], reason='Type binding is not resolved.')
                for attr_list in (c for c in node.named_children if c.type == 'attribute_list'):
                    for attr in (c for c in attr_list.named_children if c.type == 'attribute'):
                        a = text(attr.child_by_field_name('name')).split('.')[-1].removesuffix('Attribute')
                        e = observation(attr, 'csharp-attribute', a, 'candidate')
                        if a in HTTP:
                            route = literal_argument(attr)
                            endpoint = graph.node(f'csharp-endpoint:{path}:{node.start_point.row + 1}:{a}', 'endpoint', 'csharp-attribute', f'{a} {route}'.strip(), [e])
                            graph.relation('declares-endpoint', key, endpoint, 'resolved', [e])
                            graph.member('entrypoint', 'http-attribute-candidate', endpoint, [e])
                        if a in TESTS:
                            graph.member('test', 'attribute-candidate', key, [e])
        if node.type == 'invocation_expression':
            function = node.child_by_field_name('function')
            fn_name = function.child_by_field_name('name') if function else None
            generic = fn_name if fn_name and fn_name.type == 'generic_name' else None
            name = text(next((c for c in generic.named_children if c.type == 'identifier'), None)) if generic else text(fn_name or function)
            if name and SAFE.fullmatch(name):
                ev = observation(function, 'invocation', name, 'candidate')
                ref = graph.node(f'csharp-call:{path}:{node.start_point.row + 1}:{node.start_point.column}', 'call-reference', 'csharp', name, [ev])
                graph.relation('calls', parent_key, None, 'unresolved', [ev], candidates=[ref], reason='Invocation target and runtime execution are not resolved.')
                if generic and name in {'AddScoped', 'AddSingleton', 'AddTransient'}:
                    args = next((c for c in generic.named_children if c.type == 'type_argument_list'), None)
                    if args:
                        registration = graph.node(f'csharp-registration:{path}:{node.start_point.row + 1}:{node.start_point.column}', 'registration', 'csharp-di-candidate', name, [ev])
                        graph.relation('declares-registration', file_key, registration, 'resolved', [ev])
                        for index, arg in enumerate(args.named_children):
                            arg_name = text(arg)
                            if SAFE.fullmatch(arg_name):
                                ae = observation(arg, 'di-type', arg_name, 'candidate')
                                target = graph.node(f'csharp-reference:{path}:{arg_name}', 'type-reference', 'csharp', arg_name, [ae])
                                graph.relation('registers', registration, None, 'unresolved', [ae], candidates=[target], reason='Type binding and runtime registration are not resolved.', discriminator='service' if index == 0 else 'implementation')
                if name in {'MapGet', 'MapPost', 'MapPut', 'MapPatch', 'MapDelete'}:
                    route = literal_argument(node)
                    endpoint = graph.node(f'csharp-endpoint:{path}:{node.start_point.row + 1}:{node.start_point.column}', 'endpoint', 'minimal-api-candidate', f'{name} {route}'.strip(), [ev])
                    graph.relation('declares-endpoint', parent_key, endpoint, 'resolved', [ev])
                    graph.member('entrypoint', 'minimal-api-candidate', endpoint, [ev])
                if name in {'GetSection', 'GetConnectionString', 'GetValue'}:
                    config = literal_argument(node)
                    if config and CONFIG.fullmatch(config):
                        ce = observation(node, 'configuration-key', config, 'candidate')
                        setting = graph.node(f'config:{path}:{config}', 'configuration', 'csharp-candidate', config, [ce])
                        graph.relation('uses-config', parent_key, setting, 'resolved', [ce], reason='Syntactic candidate; receiver binding is not resolved.')
        for child in node.named_children:
            visit(child, namespace, parent_key, owner)

    visit(root, file_ns, file_key)
    return ('C# syntax contains errors; extracted declarations are partial.' if root.has_error else
            'C# syntax only; symbol binding, conditions, runtime behavior and full routes are not resolved.')


def extract_project(graph, source, paths):
    try:
        root = ET.fromstring(source.text)
    except ET.ParseError as exc:
        raise ValueError('invalid project XML') from exc
    path = source.path
    ev = graph.observe(source.toml_anchor('dotnet-project'), 'dotnet-project-xml', 'declaration',
                       'MSBuild conditions, properties and imports are not evaluated.')
    key = graph.node('dotnet-project:' + path, 'project', 'dotnet', PurePosixPath(path).stem, [ev])
    graph.relation('contains', 'file:' + path, key, 'resolved', [ev])
    graph.member('code', 'dotnet-project', key, [ev])
    for elem in root.iter():
        tag = elem.tag.rsplit('}', 1)[-1]
        val = elem.attrib.get('Include', '')
        if tag == 'ProjectReference' and val and not any(x in val for x in ('$(', '@(', '%(')):
            target = posixpath.normpath(posixpath.join(posixpath.dirname(path), val.replace('\\', '/')))
            if target in paths:
                graph.relation('references-project', key, None, 'unresolved', [ev], candidates=['file:' + target],
                               reason='ProjectReference declaration; MSBuild conditions are not evaluated.')
        elif tag == 'PackageReference' and SAFE.fullmatch(val):
            target = graph.node('nuget:' + val, 'dependency', 'nuget', val, [ev], external=True)
            graph.relation('declares-dependency', key, target, 'declared-external', [ev])
            if val in {'Microsoft.NET.Test.Sdk', 'xunit', 'NUnit', 'MSTest.TestFramework'}:
                graph.member('test', 'dotnet-project-candidate', key, [ev])
    return 'Project declarations only; MSBuild properties, imports and conditions are not evaluated.'
