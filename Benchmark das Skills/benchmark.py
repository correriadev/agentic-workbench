"""Measure a frozen Agentic Workbench skills checkout with the stdlib."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
import uuid

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("skills", type=Path, help="Directory containing blueprint, forge and quality-gate")
parser.add_argument("output", type=Path, help="New JSON result path")
parser.add_argument("--repeats", type=int, default=5)
args = parser.parse_args()
if args.repeats < 1:
    parser.error("--repeats must be positive")
if args.output.exists():
    parser.error("Choose a new output path to preserve the run history")

test = Path(__file__).with_name("test_contract.py")
manifest = {
    "run_id": str(uuid.uuid4()),
    "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "python": sys.version,
    "fixture_and_oracle_sha256": hashlib.sha256(test.read_bytes()).hexdigest(),
    "skills": {},
}
for name in ("blueprint", "forge", "quality-gate"):
    folder = args.skills / name
    files = {}
    for path in sorted(folder.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            data = path.read_bytes()
            files[str(path.relative_to(folder))] = {
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()
            }
    rounds = []
    for _ in range(args.repeats):
        start = time.perf_counter()
        result = subprocess.run(
            [sys.executable, str(test), str(folder / "contract.py")],
            capture_output=True, text=True, timeout=60,
        )
        rounds.append({
            "elapsed_ms": round((time.perf_counter() - start) * 1000, 2),
            "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
        })
    manifest["skills"][name] = {
        "files": files, "rounds": rounds,
        "median_ms": statistics.median(round_["elapsed_ms"] for round_ in rounds),
    }
contracts = {s["files"]["contract.py"]["sha256"] for s in manifest["skills"].values()}
manifest["contracts_identical"] = len(contracts) == 1
with args.output.open("x", encoding="utf-8") as stream:
    json.dump(manifest, stream, indent=2)
    stream.write("\n")
sys.exit(not manifest["contracts_identical"] or any(
    r["exit_code"] for skill in manifest["skills"].values() for r in skill["rounds"]
))
