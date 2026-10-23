#!/usr/bin/env python3
"""Read-only MCP stdio initialize + tools/list probe in an isolated temporary home."""
import argparse
import json
import os
import pathlib
import queue
import subprocess
import tempfile
import threading
import time


def probe(command, timeout=30):
    with tempfile.TemporaryDirectory(prefix="ai-env-mcp-") as folder:
        env = os.environ.copy()
        home = pathlib.Path(folder)
        locations = {"HOME": home, "USERPROFILE": home,
                     "LOCALAPPDATA": home / "AppData/Local", "APPDATA": home / "AppData/Roaming",
                     "XDG_CONFIG_HOME": home / ".config", "XDG_DATA_HOME": home / ".local/share",
                     "XDG_CACHE_HOME": home / ".cache", "CODEX_HOME": home / ".codex"}
        for name, location in locations.items():
            location.mkdir(parents=True, exist_ok=True)
            env[name] = str(location)
        env["DO_NOT_TRACK"] = "1"
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                                   cwd=folder, env=env)
        messages = queue.Queue()
        def read():
            for line in process.stdout:
                try:
                    messages.put(json.loads(line))
                except json.JSONDecodeError:
                    continue
            messages.put(None)
        threading.Thread(target=read, daemon=True).start()
        def send(payload):
            process.stdin.write(json.dumps(payload) + "\n")
            process.stdin.flush()
        def receive(identifier):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    message = messages.get(timeout=max(0.01, deadline-time.monotonic()))
                except queue.Empty:
                    raise TimeoutError("MCP response timed out") from None
                if message is None:
                    raise RuntimeError("MCP server exited before responding")
                if message.get("id") == identifier:
                    if "error" in message:
                        raise RuntimeError("MCP returned a protocol error")
                    return message["result"]
            raise TimeoutError("MCP response timed out")
        try:
            send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "ai-dev-environment-validation", "version": "1.0.0"}}})
            result = receive(1)
            send({"jsonrpc": "2.0", "method": "notifications/initialized"})
            send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            tools = receive(2)
            return {"initialize": True, "protocol": result.get("protocolVersion"),
                    "tools": len(tools.get("tools", [])), "paginated": bool(tools.get("nextCursor")),
                    "tool_calls": 0}
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            process.stdin.close()
            process.stdout.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=pathlib.Path)
    args = parser.parse_args()
    try:
        print(json.dumps(probe([str(args.executable.resolve(strict=True))]), indent=2))
    except (OSError, RuntimeError, TimeoutError) as error:
        parser.exit(1, "MCP probe failed: " + str(error) + "\n")
