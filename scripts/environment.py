#!/usr/bin/env python3
"""Reproduce a personal agent environment. Python 3.12+, standard library only."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import pathlib
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import tomllib
import urllib.parse
import urllib.request
import uuid
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(path):
    # JSON is a YAML 1.2 subset; keep bootstrap independent of PyYAML.
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(data):
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()


def toml_value(value):
    if isinstance(value, dict):
        return "{ " + ", ".join(json.dumps(k) + " = " + toml_value(v) for k, v in value.items()) + " }"
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(v) for v in value) + "]"
    if value is None:
        raise ValueError("TOML does not support null")
    return json.dumps(value)


def host_platform():
    system = {"Windows": "windows", "Darwin": "darwin", "Linux": "linux"}.get(platform.system())
    arch = {"AMD64": "amd64", "x86_64": "amd64", "arm64": "arm64", "aarch64": "arm64"}.get(platform.machine())
    if not system or not arch:
        raise ValueError("Unsupported OS/architecture")
    return system + "-" + arch


def contained(base, path):
    base = pathlib.Path(base).resolve()
    path = pathlib.Path(path)
    if not path.is_absolute():
        path = base / path
    # Reject links even when they currently resolve inside the destination.
    current = path
    while current != current.parent:
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError("Link/junction in managed path: " + str(current))
        current = current.parent
    if not path.resolve().is_relative_to(base) or path.resolve() == base:
        raise ValueError("Path escapes managed root: " + str(path))
    return path


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".ai-env-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextlib.contextmanager
def exclusive(state):
    state.mkdir(parents=True, exist_ok=True)
    path = state / "operation.lock"
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, str(os.getpid()).encode())
        yield
    finally:
        os.close(fd)
        path.unlink()


def download(spec, target):
    allowed = {"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com",
               "storage.googleapis.com", "nodejs.org", "www.python.org"}
    url = urllib.parse.urlparse(spec["url"])
    if url.scheme != "https" or url.hostname not in allowed or url.username or url.password:
        raise ValueError("Unapproved artifact URL")
    algorithm = spec["algorithm"]
    if algorithm not in {"sha256", "sha512"}:
        raise ValueError("Unsupported digest")
    if target.exists():
        if hashlib.new(algorithm, target.read_bytes()).hexdigest() == spec["digest"]:
            return
        raise ValueError("Cached artifact checksum mismatch: " + target.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".partial")
    try:
        request = urllib.request.Request(spec["url"], headers={"User-Agent": "ai-dev-environment/1"})
        hasher = hashlib.new(algorithm)
        with urllib.request.urlopen(request, timeout=60) as response, tmp.open("wb") as output:
            if urllib.parse.urlparse(response.url).scheme != "https":
                raise ValueError("Insecure redirect")
            while chunk := response.read(1024 * 1024):
                hasher.update(chunk)
                output.write(chunk)
        if hasher.hexdigest() != spec["digest"]:
            raise ValueError("Downloaded artifact checksum mismatch")
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()


def unpack(archive, dest):
    dest.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            for entry in z.infolist():
                contained(dest, dest / entry.filename)
                if stat.S_ISLNK(entry.external_attr >> 16):
                    raise ValueError("Archive contains symlink")
            z.extractall(dest)
    else:
        with tarfile.open(archive) as tar:
            for entry in tar.getmembers():
                contained(dest, dest / entry.name)
                if not (entry.isfile() or entry.isdir()):
                    # Node ships npm/npx links. Recreate no links: invoke npm-cli.js directly.
                    if entry.issym() and entry.name.endswith(("/bin/npm", "/bin/npx", "/bin/corepack")):
                        continue
                    raise ValueError("Archive contains link/device")
            tar.extractall(dest, members=[m for m in tar.getmembers() if m.isfile() or m.isdir()], filter="data")


def run(args, **kwargs):
    subprocess.run([str(a) for a in args], check=True, **kwargs)


class Environment:
    def __init__(self, home, system=None):
        self.home = pathlib.Path(home).absolute()
        self.state = contained(self.home, self.home / ".local/share/ai-dev-environment")
        self.system = system or host_platform()
        self.lock = load(ROOT / "environment.lock.yaml")
        self.manifest = load(ROOT / "environment.yaml")
        self.profile = load(ROOT / "profiles/personal.json")

    def source(self, name):
        return self.state / "sources" / (name + "-" + self.lock["sources"][name]["commit"])

    def binary_root(self, name):
        item = self.lock["binaries"][name]
        if self.system not in item["platforms"]:
            raise ValueError(name + " has no locked artifact for " + self.system)
        return self.state / "binaries" / (name + "-" + item["version"] + "-" + self.system)

    def binary(self, name):
        root = self.binary_root(name)
        spec = self.lock["binaries"][name]["platforms"][self.system]
        exe = spec["executable"] + (".exe" if self.system.startswith("windows") else "")
        if name == "node":
            stem = pathlib.Path(urllib.parse.urlparse(spec["url"]).path).name
            stem = stem.removesuffix(".tar.gz").removesuffix(".zip")
            return root / stem / ("" if self.system.startswith("windows") else "bin") / exe
        return root / exe

    def process_env(self):
        env = os.environ.copy()
        env["DO_NOT_TRACK"] = "1"
        if self.home.resolve() != pathlib.Path.home().resolve():
            env.update(HOME=str(self.home), USERPROFILE=str(self.home),
                       APPDATA=str(self.home / "AppData/Roaming"),
                       LOCALAPPDATA=str(self.home / "AppData/Local"),
                       XDG_CONFIG_HOME=str(self.home / ".config"),
                       XDG_DATA_HOME=str(self.home / ".local/share"),
                       XDG_CACHE_HOME=str(self.home / ".cache"),
                       CODEX_HOME=str(self.home / ".codex"),
                       OPENCODE_CONFIG_DIR=str(self.home / ".config/opencode"))
            for name in ["OPENCODE_CONFIG", "OPENCODE_CONFIG_CONTENT"]:
                env.pop(name, None)
        env["PATH"] = os.pathsep.join([str(self.binary(n).parent) for n in self.manifest["binaries"]] +
                                      [str(self.state / "node-tools/node_modules/.bin"), env.get("PATH", "")])
        return env

    def fetch(self, upstream_cbm=False):
        for name in self.manifest["sources"]:
            target = contained(self.state, self.source(name))
            spec = self.lock["sources"][name]
            if not re.fullmatch(r"[0-9a-f]{40}", spec["commit"]) or not spec["url"].startswith("https://github.com/"):
                raise ValueError("Invalid source pin")
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                # Failed checkout is recoverable; never mark it ready until HEAD matches.
                run(["git", "clone", "-c", "core.longpaths=true", "--no-checkout", "--filter=blob:none", spec["url"], target])
                run(["git", "-c", "core.longpaths=true", "-C", target, "checkout", "--detach", spec["commit"]])
            actual = subprocess.check_output(["git", "-C", str(target), "rev-parse", "HEAD"], text=True).strip()
            dirty = subprocess.check_output(["git", "-C", str(target), "status", "--porcelain"], text=True).strip()
            if actual != spec["commit"] or dirty:
                raise ValueError("Source checkout changed: " + name)
        for name in self.manifest["binaries"] + (["codebase-memory-upstream"] if upstream_cbm else []):
            spec = self.lock["binaries"][name]["platforms"].get(self.system)
            if spec is None:
                raise ValueError("No locked " + name + " for " + self.system)
            root = contained(self.state, self.binary_root(name))
            exe = self.binary(name)
            marker = root / ".artifact.json"
            if marker.exists():
                if load(marker).get("sha256") != digest(exe.read_bytes()):
                    raise ValueError("Installed binary changed: " + name)
                continue
            archive = contained(self.state, self.state / "downloads" / (spec["digest"] + spec["archive"]))
            print("Fetch", name, self.lock["binaries"][name]["version"], flush=True)
            download(spec, archive)
            with tempfile.TemporaryDirectory(dir=self.state) as temp:
                staging = pathlib.Path(temp)
                if spec["archive"] == ".exe":
                    shutil.copyfile(archive, staging / exe.name)
                else:
                    unpack(archive, staging)
                if name == "node":
                    payload = staging
                else:
                    candidates = [p for p in staging.rglob(exe.name) if p.is_file()]
                    if len(candidates) != 1:
                        raise ValueError("Ambiguous executable in archive")
                    payload = staging / "payload"
                    payload.mkdir()
                    shutil.copyfile(candidates[0], payload / exe.name)
                if root.exists():
                    raise ValueError("Incomplete binary directory: remove only after inspection: " + str(root))
                shutil.copytree(payload, root)
            exe.chmod(exe.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            atomic(marker, dump({"sha256": digest(exe.read_bytes()), "artifact_digest": spec["digest"]}))
        tools = contained(self.state, self.state / "node-tools")
        tools.mkdir(parents=True, exist_ok=True)
        lock_data = (ROOT / "integrations/node/package-lock.json").read_bytes()
        marker = tools / ".lock-sha256"
        if not marker.exists() or marker.read_text() != digest(lock_data):
            for filename in ["package.json", "package-lock.json"]:
                shutil.copyfile(ROOT / "integrations/node" / filename, tools / filename)
            node = self.binary("node")
            npm = node.parent / "node_modules/npm/bin/npm-cli.js" if self.system.startswith("windows") else node.parent.parent / "lib/node_modules/npm/bin/npm-cli.js"
            run([node, npm, "ci", "--no-audit", "--no-fund", "--prefix", tools], env=self.process_env())
            atomic(marker, digest(lock_data).encode())
        generated = contained(self.state, self.state / "generated/opencode-agents")
        generated.mkdir(parents=True, exist_ok=True)
        adapter = self.source("caveman") / "installer/lib/opencode-agent.js"
        program = "const fs=require('node:fs');const a=require(process.argv[1]);fs.writeFileSync(process.argv[3],a.transformOpencodeAgentFrontmatter(fs.readFileSync(process.argv[2],'utf8'),{subagent:true}));"
        for name in ["cavecrew-builder", "cavecrew-investigator", "cavecrew-reviewer"]:
            run([self.binary("node"), "-e", program, adapter,
                 self.source("caveman") / "agents" / (name + ".md"), generated / (name + ".md")])

    def render(self, text):
        return text.replace("__HOME__", self.home.as_posix()).encode("utf-8")

    def desired(self, agents, upstream_cbm=False, custom_cbm=None):
        files = {}
        missing = []

        def put(path, data):
            target = contained(self.home, self.home / path)
            if target.suffix == ".toml":
                tomllib.loads(data.decode("utf-8-sig"))
            if target in files and files[target] != data:
                raise ValueError("Conflicting desired target")
            files[target] = data

        def tree(source, dest):
            if not source.exists():
                missing.append(str(source))
                return
            for p in sorted(source.rglob("*")):
                if p.is_file() and not p.is_symlink() and not any(x in p.relative_to(source).parts for x in ["__pycache__", "node_modules", ".git"]):
                    raw = p.read_bytes()
                    if b"\x00" in raw:
                        put(dest / p.relative_to(source), raw)
                    else:
                        put(dest / p.relative_to(source), self.render(raw.decode("utf-8-sig")))

        for agent in agents:
            skill_roots = {"codex": [".codex/skills"], "opencode": [".config/opencode/skills"],
                           "antigravity": [".gemini/config/skills", ".gemini/antigravity-cli/skills"]}[agent]
            for skills in skill_roots:
                for item in self.profile["skills"]:
                    if item["name"].startswith("jev-"):
                        continue
                    tree(ROOT / item["source"], pathlib.Path(skills) / item["name"])
                for name in self.profile["third_party_skills"]:
                    tree(self.source("caveman") / "skills" / name, pathlib.Path(skills) / name)
                for name in ["ponytail", "ponytail-audit", "ponytail-debt", "ponytail-gain", "ponytail-help", "ponytail-review"]:
                    tree(self.source("ponytail") / "skills" / name, pathlib.Path(skills) / name)
            agents_dest = {"codex": ".codex/agents", "opencode": ".config/opencode/agents"}.get(agent)
            if agents_dest:
                tree(ROOT / "integrations" / agent / "agents", pathlib.Path(agents_dest))
            instructions = {"codex": ".codex/AGENTS.md", "opencode": ".config/opencode/AGENTS.md", "antigravity": ".gemini/GEMINI.md"}[agent]
            put(instructions, self.render((ROOT / "integrations" / agent / "instructions.md").read_text(encoding="utf-8")))
            if agent == "codex":
                path = contained(self.home, self.home / ".codex/config.toml")
                config_text = path.read_text(encoding="utf-8") if path.exists() else ""
                config = tomllib.loads(config_text)
                preferences = load(ROOT / "integrations/codex/preferences.json")
                prefix = []
                for key, value in preferences.items():
                    if key not in config and not isinstance(value, dict):
                        prefix.append(key + " = " + toml_value(value))
                if prefix:
                    config_text = "\n".join(prefix) + "\n" + config_text
                for key, value in preferences.items():
                    if key not in config and isinstance(value, dict):
                        config_text += "\n[" + key + "]\n" + "\n".join(json.dumps(k) + " = " + toml_value(v) for k, v in value.items()) + "\n"
                put(".codex/config.toml", config_text.encode())
                put(".codex/RTK.md", self.render((ROOT / "integrations/codex/RTK.md").read_text()))
                hooks_path = contained(self.home, self.home / ".codex/hooks.json")
                hooks = load(hooks_path) if hooks_path.exists() else {"hooks": {}}
                entries = hooks.setdefault("hooks", {})
                desired_hooks = {
                    "SessionStart": {"hooks": [{"type": "command", "command": self.node_command(self.source("caveman") / ".codex/codex-sessionstart.js")}]},
                    "PreToolUse": {"matcher": "Bash", "hooks": [{"type": "command", "command": self.command(self.binary("rtk")) + " hook codex"}]},
                }
                for event, entry in desired_hooks.items():
                    values = entries.setdefault(event, [])
                    # Existing tools own their hooks. Flag differing versions for review rather than stack duplicate rewriters.
                    if entry not in values:
                        if any(any(any(tool in h.get("command", "").lower() for tool in ["rtk", "caveman"]) for h in x.get("hooks", [])) for x in values):
                            missing.append("existing " + event + " hook requires migration review")
                        else:
                            values.append(entry)
                put(".codex/hooks.json", dump(hooks))
            if agent == "opencode":
                tree(self.state / "generated/opencode-agents", pathlib.Path(".config/opencode/agents"))
                plugin_root = pathlib.Path(".config/opencode/plugins/caveman")
                for name in ["package.json", "plugin.js", "server.js"]:
                    p = self.source("caveman") / "src/plugins/opencode" / name
                    if p.exists():
                        put(plugin_root / name, p.read_bytes())
                    else:
                        missing.append(str(p))
                for stem in ["caveman-config", "caveman-parse"]:
                    p = self.source("caveman") / "src/hooks" / (stem + ".js")
                    if p.exists():
                        put(plugin_root / (stem + ".cjs"), p.read_bytes())
                    else:
                        missing.append(str(p))
                tree(self.source("caveman") / "src/plugins/opencode/commands", pathlib.Path(".config/opencode/commands"))
                rtk_plugin = self.source("rtk") / "hooks/opencode/rtk.ts"
                if rtk_plugin.exists():
                    put(".config/opencode/plugins/rtk.ts", rtk_plugin.read_bytes())
                else:
                    missing.append(str(rtk_plugin))
                path = contained(self.home, self.home / ".config/opencode/opencode.jsonc")
                # Parse JSON only. Preserve JSONC with comments by refusing an automatic rewrite.
                config = load(path) if path.exists() else {"$schema": "https://opencode.ai/config.json"}
                refs = config.setdefault("plugin", [])
                for ref in [str(self.source("ponytail") / ".opencode/plugins/ponytail.mjs"), "./plugins/caveman"]:
                    if ref not in refs:
                        if "ponytail" in ref and any("ponytail" in x for x in refs):
                            missing.append("existing Ponytail plugin requires pin migration review")
                        else:
                            refs.append(ref)
                if upstream_cbm or custom_cbm:
                    config.setdefault("mcp", {})["codebase-memory-mcp"] = {"type": "local", "command": [str(custom_cbm or self.binary("codebase-memory-upstream"))]}
                put(".config/opencode/opencode.jsonc", dump(config))
            if agent == "antigravity":
                config_path = contained(self.home, self.home / ".gemini/config/config.json")
                config = load(config_path) if config_path.exists() else {}
                preferences = load(ROOT / "integrations/antigravity/preferences.json")
                for key, value in preferences.get("userSettings", {}).items():
                    config.setdefault("userSettings", {}).setdefault(key, value)
                put(".gemini/config/config.json", dump(config))
                # Antigravity 1.4.6 common config plugin path, observed locally and verified in RTK v1.0.1 source.
                put(".gemini/config/plugins/rtk/plugin.json", dump({"name": "rtk", "version": "1.0.0"}))
                put(".gemini/config/plugins/rtk/hooks.json", dump({"rtk-rewrite": {"enabled": True, "PreToolUse": [{"matcher": "run_command", "hooks": [{"type": "command", "command": self.command(self.binary("rtk")) + " hook antigravity", "timeout": 10}]}]}}))
                if upstream_cbm or custom_cbm:
                    path = contained(self.home, self.home / ".gemini/config/mcp_config.json")
                    config = load(path) if path.exists() else {"mcpServers": {}}
                    config.setdefault("mcpServers", {})["codebase-memory-mcp"] = {"command": str(custom_cbm or self.binary("codebase-memory-upstream")), "args": []}
                    put(".gemini/config/mcp_config.json", dump(config))
            if agent == "codex" and (upstream_cbm or custom_cbm):
                path = contained(self.home, self.home / ".codex/config.toml")
                text = files[path].decode()
                config = tomllib.loads(text)
                exe = str(custom_cbm or self.binary("codebase-memory-upstream"))
                existing = config.get("mcp_servers", {}).get("codebase-memory-mcp")
                if existing is not None:
                    if existing.get("command") != exe:
                        missing.append("existing Codex MCP command requires migration review")
                else:
                    text += '\n[mcp_servers.codebase-memory-mcp]\ncommand = ' + json.dumps(exe) + '\n'
                # Amend the same native config after preference rendering.
                tomllib.loads(text)
                files[path] = text.encode()
        paths = [str(self.binary(n).parent) for n in self.manifest["binaries"]] + [str(self.state / "node-tools/node_modules/.bin")]
        # Escape for both shells, including home directories with spaces and metacharacters.
        ps_value = os.pathsep.join(paths).replace("'", "''")
        sh_value = ":".join(p.replace("\\", "/") for p in paths).replace("'", "'\"'\"'")
        put(".local/share/ai-dev-environment/env.ps1", ("$env:DO_NOT_TRACK='1'\n$env:PATH='" + ps_value + "'+[IO.Path]::PathSeparator+$env:PATH\n").encode())
        put(".local/share/ai-dev-environment/env.sh", ("export DO_NOT_TRACK=1\nexport PATH='" + sh_value + "':\"$PATH\"\n").encode())
        return files, missing

    @staticmethod
    def command(path):
        value = str(path)
        if any(c in value for c in ['"', '$', '`', '\n', '\r', '%']):
            raise ValueError("Home path cannot safely be represented in a cross-agent hook")
        return '"' + value + '"'

    def node_command(self, script):
        return self.command(self.binary("node")) + " " + self.command(script)

    def assess(self, files):
        installed = load(self.state / "managed.json") if (self.state / "managed.json").exists() else {}
        result = []
        for path, data in sorted(files.items()):
            old = path.read_bytes() if path.exists() else None
            relative = path.relative_to(self.home).as_posix()
            action = "same" if old == data else "create" if old is None else "update" if installed.get(relative) == digest(old) else "conflict"
            result.append((path, data, old, action))
        return result

    def apply(self, files, replace=False):
        rows = self.assess(files)
        conflicts = [str(p.relative_to(self.home)) for p, _, _, a in rows if a == "conflict"]
        if conflicts and not replace:
            raise ValueError("Unmanaged/edited files preserved; inspect conflicts before --replace:\n" + "\n".join(conflicts))
        changed = [row for row in rows if row[3] != "same"]
        if not changed:
            print("No changes")
            return None
        txid = time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
        tx = contained(self.state, self.state / "transactions" / txid)
        tx.mkdir(parents=True, mode=0o700)
        journal = {"home": str(self.home), "status": "applying", "changes": []}
        # Include the ownership manifest itself in recovery.
        managed = contained(self.home, self.state / "managed.json")
        mapping = load(managed) if managed.exists() else {}
        for p, data in files.items():
            mapping[p.relative_to(self.home).as_posix()] = digest(data)
        changed.append((managed, dump(mapping), managed.read_bytes() if managed.exists() else None, "update"))
        for i, (p, data, old, _) in enumerate(changed):
            backup = str(i) if old is not None else None
            if old is not None:
                atomic(tx / backup, old)
            journal["changes"].append({"path": p.relative_to(self.home).as_posix(), "backup": backup,
                                       "before": digest(old) if old is not None else None, "after": digest(data)})
        atomic(tx / "journal.json", dump(journal))
        try:
            for p, data, _, _ in changed:
                contained(self.home, p)
                atomic(p, data)
            journal["status"] = "applied"
            atomic(tx / "journal.json", dump(journal))
        except BaseException:
            # Restore files that reached the expected after-state. Leave unrelated edits intact.
            self.rollback(txid, interrupted=True)
            raise
        print("Applied", len(changed)-1, "files; transaction", txid)
        return txid

    def rollback(self, txid, interrupted=False):
        if not re.fullmatch(r"[0-9T-]+[0-9a-f]{8}", txid):
            raise ValueError("Invalid transaction ID")
        tx = contained(self.state, self.state / "transactions" / txid)
        journal = load(tx / "journal.json")
        if pathlib.Path(journal["home"]) != self.home:
            raise ValueError("Transaction belongs to another home")
        if journal["status"] == "rolled-back":
            print("Already rolled back")
            return
        actions = []
        for entry in reversed(journal["changes"]):
            path = contained(self.home, self.home / entry["path"])
            actual = digest(path.read_bytes()) if path.exists() else None
            if actual == entry["before"]:
                continue
            if actual != entry["after"]:
                raise ValueError("Refusing to overwrite post-install edit: " + entry["path"])
            old = None
            if entry["backup"] is not None:
                old = contained(tx, tx / entry["backup"]).read_bytes()
                if digest(old) != entry["before"]:
                    raise ValueError("Backup checksum mismatch")
            actions.append((path, old))
        for path, old in actions:
            if old is None:
                path.unlink()
            else:
                atomic(path, old)
        journal["status"] = "rolled-back"
        atomic(tx / "journal.json", dump(journal))
        print("Rolled back", txid)

    def doctor(self, agents):
        failures = []
        for name in self.manifest["binaries"]:
            exe = self.binary(name)
            if not exe.exists():
                failures.append("missing binary: " + name)
                continue
            marker = self.binary_root(name) / ".artifact.json"
            if not marker.exists() or load(marker).get("sha256") != digest(exe.read_bytes()):
                failures.append("binary integrity: " + name)
            result = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=30, env=self.process_env())
            expected = self.lock["binaries"][name]["version"]
            if result.returncode or expected not in result.stdout + result.stderr:
                failures.append("version mismatch: " + name)
        for agent in agents:
            if agent == "antigravity":
                continue
            node = self.binary("node")
            script = self.state / "node-tools/node_modules" / ("@openai/codex/bin/codex.js" if agent == "codex" else "opencode-ai/bin/opencode.exe")
            if not node.exists() or not script.exists():
                failures.append("missing agent: " + agent)
                continue
            command = [str(node), str(script)] if agent == "codex" else [str(script)]
            result = subprocess.run(command + ["--version"], capture_output=True, text=True, timeout=30, env=self.process_env())
            if result.returncode or self.lock["npm"][agent]["version"] not in result.stdout + result.stderr:
                failures.append("agent version: " + agent)
        manifest = self.state / "managed.json"
        if not manifest.exists():
            failures.append("configuration has not been applied")
        else:
            for path, expected in load(manifest).items():
                target = contained(self.home, self.home / path)
                if not target.exists() or digest(target.read_bytes()) != expected:
                    failures.append("configuration drift: " + path)
        print(json.dumps({"platform": self.system, "scope": "core binaries and managed configuration",
                          "full_baseline_complete": False, "failures": failures,
                          "pending_baseline": ["custom CBM provenance/fresh-home startup", "Open Graph", "Jev provenance", "app plugins"],
                          "manual_checks": ["agent authentication", "Codex /hooks trust", "MCP initialize/tools/list", "model access", "Antigravity plugin activation"]}, indent=2))
        return not failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "fetch", "apply", "install", "doctor", "rollback"])
    parser.add_argument("--home", type=pathlib.Path, default=pathlib.Path.home())
    parser.add_argument("--agents", nargs="+", choices=["codex", "antigravity", "opencode"], default=["codex", "antigravity", "opencode"])
    parser.add_argument("--replace", action="store_true", help="Back up and replace reviewed configuration conflicts")
    parser.add_argument("--upstream-cbm", action="store_true", help="Explicitly select upstream CBM; differs from the installed custom fork")
    parser.add_argument("--custom-cbm", type=pathlib.Path, help="Existing exact custom binary, verified against inventory SHA-256")
    parser.add_argument("--transaction")
    args = parser.parse_args()
    env = Environment(args.home)
    if args.custom_cbm and args.upstream_cbm:
        parser.error("Choose one CBM implementation")
    if args.custom_cbm:
        args.custom_cbm = args.custom_cbm.resolve(strict=True)
        if digest(args.custom_cbm.read_bytes()) != env.lock["local_codebase_memory"]["sha256"]:
            raise ValueError("Custom CBM does not match inventoried binary")
    if args.command == "doctor":
        return 0 if env.doctor(args.agents) else 1
    if args.command == "plan":
        files, missing = env.desired(args.agents, args.upstream_cbm, args.custom_cbm)
        counts = {}
        conflicts = []
        for p, _, _, action in env.assess(files):
            counts[action] = counts.get(action, 0) + 1
            if action == "conflict":
                conflicts.append(p.relative_to(env.home).as_posix())
        print(json.dumps({"platform": env.system, "changes": counts, "conflicts": conflicts,
                          "unavailable": sorted(set(missing)), "network": False, "writes": False}, indent=2))
        return 0
    with exclusive(env.state):
        if args.command == "rollback":
            if not args.transaction:
                parser.error("rollback requires --transaction")
            env.rollback(args.transaction)
            return 0
        if args.command in ["fetch", "install"]:
            env.fetch(args.upstream_cbm)
        if args.command in ["apply", "install"]:
            files, missing = env.desired(args.agents, args.upstream_cbm, args.custom_cbm)
            if missing:
                raise ValueError("Cannot apply incomplete configuration; fetch dependencies or review migration:\n" + "\n".join(sorted(set(missing))))
            env.apply(files, args.replace)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print("ERROR:", str(exc), file=sys.stderr)
        raise SystemExit(1)
