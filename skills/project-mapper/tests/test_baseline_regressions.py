"""Black-box regressions for the optional static Python scan."""

import unittest

from test_acceptance import fixture, invoke, rows, test_directory


class StaticScan(unittest.TestCase):
    def test_unclassified_application_remains_unexamined(self):
        with test_directory() as repo:
            rev = fixture(repo, {
                'lib/main.dart': 'void main() {}\n',
                'pubspec.yaml': 'name: app\n',
                'infra/main.tf': 'variable "region" { type = string }\n',
                'contracts/service.yaml': 'openapi: 3.0.0\n',
            })
            invoke(repo, 'build', '--commit', rev)
            self.assertEqual(invoke(repo, 'verify')['status'], 'partial')
            self.assertEqual(invoke(repo, 'coverage')['inventory_counts'], {'unexamined': 4})

    def test_import_scope_and_builtin_precedence(self):
        with test_directory() as repo:
            rev = fixture(repo, {
                'acquirer.py': 'def pay():\n    return 1\n',
                'sandbox_payments.py': 'def pay():\n    return 0\n',
                'time.py': 'def monotonic():\n    return 123\n',
                'app.py': 'from acquirer import pay\nimport time\n'
                          'def settle():\n    return pay()\n'
                          'def fixture():\n    from sandbox_payments import pay\n    return pay()\n'
                          'def now():\n    return time.monotonic()\n',
            })
            invoke(repo, 'build', '--commit', rev)
            real = invoke(repo, 'trace', 'function:app:settle', '--type', 'calls')
            self.assertEqual([e['target'] for e in real['edges']], ['function:acquirer:pay'])
            local = invoke(repo, 'node', 'function:app:fixture')['nodes'][0]
            local_call, = [edge for edge in local['outgoing'] if edge['type'] == 'calls']
            self.assertEqual(local_call['candidates'], ['function:sandbox_payments:pay'])
            clock = invoke(repo, 'node', 'function:app:now')['nodes'][0]
            calls = [edge for edge in clock['outgoing'] if edge['type'] == 'calls']
            self.assertEqual([(e['state'], e['candidates']) for e in calls], [('unresolved', [])])
            self.assertIn(('external-module:time',), rows(
                repo, "SELECT target FROM relationships WHERE type='imports' AND source='module:app'"))

    def test_dynamic_dependencies_report_structural_gap(self):
        with test_directory() as repo:
            rev = fixture(repo, {
                'pyproject.toml': '[project]\nname = "shop"\ndynamic = ["dependencies"]\n'
                                  '[tool.setuptools.dynamic]\ndependencies = { file = ["requirements.txt"] }\n',
                'requirements.txt': 'requests>=2\n',
            })
            invoke(repo, 'build', '--commit', rev)
            row, = invoke(repo, 'coverage', '--area', '.', '--family', 'structural')['coverage']
            self.assertEqual(row['status'], 'partial')
            self.assertFalse(row['scoped_absence'])
            self.assertIn('dynamic', row['reason'])

    def test_trace_limits_coverage_to_reached_areas(self):
        with test_directory() as repo:
            rev = fixture(repo, {
                'billing/__init__.py': '', 'billing/worker.py': 'def pay():\n    return 1\n',
                'billing/entry.py': 'from .worker import pay\ndef settle():\n    return pay()\n',
                'inventory/__init__.py': '', 'inventory/entry.py': 'def run(driver):\n    return driver.fetch()\n',
            })
            invoke(repo, 'build', '--commit', rev)
            trace = invoke(repo, 'trace', 'function:billing.entry:settle', '--type', 'calls')
            self.assertEqual(len(trace['edges']), 1)
            self.assertEqual(trace['coverage_frontier'], [])
            self.assertFalse(trace['analysis_incomplete'])
            self.assertEqual(trace['repository_status'], 'partial')


if __name__ == '__main__':
    unittest.main()
