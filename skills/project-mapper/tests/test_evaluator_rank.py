"""Network-free checks for the optional benchmark arm."""
import io
import json
import os
import unittest
from unittest.mock import patch

from evaluator.rea_ranges import ranked


class RankFallback(unittest.TestCase):
    @patch.dict(os.environ, {'TYPESAFE_API_KEY': 'fixture'})
    @patch('urllib.request.build_opener')
    def test_timeout_and_invalid_choice_keep_the_entire_local_order(self, opener):
        paths = ['ci.yml', 'website-pages.yml', 'pages.yml']
        expected = ranked(paths, False, {})
        malformed = json.dumps({'answers': {'next': {'type': 'choice', 'probabilities': {'p0': 1}}}})
        opener.return_value.open.side_effect = [TimeoutError(), io.BytesIO(malformed.encode())]
        for failure in ('TimeoutError', 'ValueError'):
            stats = {}
            self.assertEqual(ranked(paths, True, stats), expected)
            self.assertEqual((stats['attempted'], stats['applied'], stats['fallback']), (1, 0, failure))
