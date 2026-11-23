"""Credential values must not be persisted by the multidimensional map."""

import unittest
from uuid import uuid4

from test_acceptance import fixture, invoke, test_directory


class MultidimensionalCredentials(unittest.TestCase):
    def test_values_in_common_source_and_configuration_contexts_are_not_persisted(self):
        with test_directory() as repo:
            secret = 'synthetic-credential-' + uuid4().hex
            revision = fixture(repo, {
                'package.json': '{"scripts":{"start":"TOKEN=' + secret + ' node script.mjs"}}\n',
                'mcp.json': '{"mcpServers":{"service":{"env":{"TOKEN":"' + secret +
                            '"},"args":["' + secret + '"]}}}\n',
                'website/wrangler.toml': 'main = "worker.mjs"\n[vars]\nTOKEN = "' + secret + '"\n',
                'src/app.ts': 'const token = "' + secret + '";\n',
                'settings.env': 'TOKEN=' + secret + '\n',
                'secrets.py': 'TOKEN = "' + secret + '"\n',
            })
            invoke(repo, 'map', '--commit', revision)
            self.assertEqual(invoke(repo, 'verify')['integrity'], 'ok')
            for artifact in (repo / '.project-mapper').rglob('*'):
                if artifact.is_file():
                    with self.subTest(artifact=str(artifact.relative_to(repo))):
                        self.assertNotIn(secret.encode(), artifact.read_bytes())


if __name__ == '__main__':
    unittest.main()
