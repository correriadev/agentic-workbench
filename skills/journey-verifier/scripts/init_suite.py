"""Initialize a separate E2E checkout or resume an existing one."""
import argparse
import json
from pathlib import Path
import subprocess


def git(directory, *args, check=True):
    return subprocess.run(["git", "-C", str(directory), *args], text=True,
                          capture_output=True, check=check)


def prepare(target, suite):
    target = Path(git(target.resolve(strict=True), "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    revision = git(target, "rev-parse", "--verify", "HEAD").stdout.strip()
    suite = suite.resolve()
    if target.is_relative_to(suite) or suite.is_relative_to(target):
        raise ValueError("Target and suite must be disjoint directories")
    if suite.exists():
        top = git(suite, "rev-parse", "--show-toplevel", check=False)
        if top.returncode or Path(top.stdout.strip()).resolve() != suite:
            raise ValueError("Existing destination must be a separate Git root")
    else:
        parent = next(path for path in suite.parents if path.exists())
        if git(parent, "rev-parse", "--show-toplevel", check=False).returncode == 0:
            raise ValueError("Choose a destination outside other working trees")
        suite.mkdir(parents=True)
        git(suite, "init", "--quiet")
    return {"target": str(target), "source_revision": revision, "suite": str(suite),
            "source_dirty": bool(git(target, "status", "--porcelain").stdout)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("suite", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.target, args.suite)))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{error}\n")
