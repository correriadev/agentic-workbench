#!/usr/bin/env python3
"""Offline repository integrity, secret-pattern and manifest checks."""
import hashlib
import json
import pathlib
import re
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def verify():
    errors = []
    def read(path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    lock = read("environment.lock.yaml")
    manifest = read("environment.yaml")
    profile = read("profiles/personal.json")
    for source in lock["sources"].values():
        if not re.fullmatch(r"[0-9a-f]{40}", source["commit"]):
            errors.append("mutable source reference")
    for name, item in lock["binaries"].items():
        for spec in item["platforms"].values():
            size = 64 if spec["algorithm"] == "sha256" else 128
            if not re.fullmatch(r"[0-9a-f]{" + str(size) + "}", spec["digest"]):
                errors.append("invalid artifact digest: " + name)
    for item in profile["skills"]:
        source = (ROOT / item["source"]).resolve()
        if not source.is_relative_to(ROOT) or not (source / "SKILL.md").exists():
            errors.append("invalid skill source: " + item["source"])
    skill_signatures = {}
    for folder in sorted((ROOT / "skills/authored").iterdir()):
        if not folder.is_dir():
            continue
        files = sorted(p for p in folder.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        if any(p.name == "openai.yaml" for p in files):
            errors.append("provider-specific skill metadata: " + folder.name)
        signature = hashlib.sha256(b"".join(p.relative_to(folder).as_posix().encode() + b"\0" + p.read_bytes() for p in files)).hexdigest()
        if signature in skill_signatures:
            errors.append("duplicate skill trees: " + skill_signatures[signature] + ", " + folder.name)
        skill_signatures[signature] = folder.name
    npm = read("integrations/node/package-lock.json")
    for entry, package in npm["packages"].items():
        if entry and ("integrity" not in package or not package.get("resolved", "").startswith("https://registry.npmjs.org/")):
            errors.append("unlocked npm package: " + entry)
    for name in manifest["npm"]:
        item = lock["npm"][name]
        installed = npm["packages"]["node_modules/" + item["name"]]
        if installed["version"] != item["version"] or installed["integrity"] != item["integrity"]:
            errors.append("npm lock mismatch: " + name)
    integrity = read("profiles/assets.sha256.json")
    actual = {}
    for folder in ["skills/authored", "integrations/codex", "integrations/antigravity", "integrations/opencode"]:
        for path in (ROOT / folder).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                actual[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != integrity:
        errors.append("asset manifest differs; inspect changes before refreshing hashes")
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(p in {".git", ".work", ".state", "node_modules", "__pycache__"} for p in relative.parts) or not path.is_file():
            continue
        data = path.read_bytes()
        if re.search(rb"(?:sk-[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY)", data):
            errors.append("potential credential: " + relative.as_posix())
        if path.name.lower() in {"auth.json", ".env", "credentials.json"}:
            errors.append("forbidden credential file: " + relative.as_posix())
        if path.suffix == ".toml":
            try:
                tomllib.loads(data.decode("utf-8-sig"))
            except (ValueError, UnicodeDecodeError):
                errors.append("invalid TOML: " + relative.as_posix())
        if relative.parts[0] == "docs" and path.suffix == ".md" and len(data.decode("utf-8")) > 10000:
            errors.append("documentation exceeds 10000 characters: " + relative.as_posix())
    print(json.dumps({"errors": errors, "asset_files": len(actual), "npm_packages": len(npm["packages"])-1}, indent=2))
    return not errors


if __name__ == "__main__":
    sys.exit(0 if verify() else 1)
