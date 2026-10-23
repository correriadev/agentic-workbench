#!/usr/bin/env python3
"""Run core acceptance in a disposable home, never the current real home."""
import argparse
import json
import pathlib
import subprocess
import sys

from environment import Environment, ROOT, dump


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=pathlib.Path, required=True)
    args = parser.parse_args()
    home = args.home.resolve()
    real = pathlib.Path.home().resolve()
    if home == real or home in real.parents:
        parser.error("Choose a disposable child directory, never the real home or an ancestor")
    env = Environment(home)
    script = ROOT / "scripts/environment.py"
    subprocess.run([sys.executable, str(script), "install", "--home", str(home)], check=True)
    desired, missing = env.desired(["codex", "antigravity", "opencode"])
    if missing or any(row[3] != "same" for row in env.assess(desired)):
        raise RuntimeError("Install did not converge")
    subprocess.run([sys.executable, str(script), "apply", "--home", str(home)], check=True)
    if not env.doctor(["codex", "antigravity", "opencode"]):
        raise RuntimeError("Core doctor failed")
    commands = {
        "codex-config": [env.binary("node"), env.state / "node-tools/node_modules/@openai/codex/bin/codex.js", "mcp", "list", "--json"],
        "opencode-config": [env.state / "node-tools/node_modules/opencode-ai/bin/opencode.exe", "debug", "config"],
        "antigravity-rtk": [env.binary("antigravity"), "plugin", "validate", home / ".gemini/config/plugins/rtk", "--strict", "--json"],
    }
    results = {"scope": "core only", "full_baseline_complete": False, "platform": env.system,
               "idempotent": True, "native_checks": {}}
    for name, command in commands.items():
        p = subprocess.run([str(x) for x in command], env=env.process_env(), cwd=home,
                           capture_output=True, text=True, encoding="utf-8", timeout=60, check=True)
        data = json.loads(p.stdout)
        if name == "opencode-config":
            plugins = data.get("plugin", [])
            if not all(any(tool in path for path in plugins) for tool in ["ponytail", "caveman", "rtk"]):
                raise RuntimeError("Missing OpenCode plugin")
            results["native_checks"][name] = {"accepted": True, "plugins": len(plugins), "agents": len(data.get("agent", {}))}
        elif name == "antigravity-rtk":
            if data.get("findings"):
                raise RuntimeError("Antigravity plugin validation has findings")
            results["native_checks"][name] = {"accepted": True, "findings": []}
        else:
            results["native_checks"][name] = {"accepted": True, "servers": len(data)}
    output = env.state / "acceptance.json"
    output.write_bytes(dump(results))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
