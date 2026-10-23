import importlib.util
import pathlib
import sys
import unittest

SPEC = importlib.util.spec_from_file_location("check_mcp", pathlib.Path(__file__).resolve().parents[1] / "scripts/check_mcp.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class ProtocolProbeTests(unittest.TestCase):
    def test_initialize_and_tools_list_without_tool_calls(self):
        program = '''import json,sys
for line in sys.stdin:
 r=json.loads(line)
 if r['method']=='initialize':
  print(json.dumps({'jsonrpc':'2.0','id':r['id'],'result':{'protocolVersion':'2024-11-05','capabilities':{}}}),flush=True)
 elif r['method']=='tools/list':
  print(json.dumps({'jsonrpc':'2.0','id':r['id'],'result':{'tools':[{'name':'example'}]}}),flush=True)
 elif r['method']!='notifications/initialized':
  sys.exit(2)
'''
        result = m.probe([sys.executable, "-u", "-c", program], timeout=5)
        self.assertEqual(result["tools"], 1)
        self.assertEqual(result["tool_calls"], 0)

    def test_unresponsive_server_has_bounded_timeout(self):
        with self.assertRaises(TimeoutError):
            m.probe([sys.executable, "-u", "-c", "import time;time.sleep(10)"], timeout=0.1)

    def test_exited_server_fails_explicitly(self):
        with self.assertRaisesRegex(RuntimeError, "exited"):
            m.probe([sys.executable, "-c", "pass"], timeout=5)
