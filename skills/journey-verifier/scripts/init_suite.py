"""Initialize a separate E2E checkout or resume an existing one."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def git(directory, *args, check=True):
    return subprocess.run(["git", "-C", str(directory), *args], text=True,
                          capture_output=True, check=check)


def initialize_suite(suite):
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


def prepare(target, suite):
    target = Path(git(target.resolve(strict=True), "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    revision = git(target, "rev-parse", "--verify", "HEAD").stdout.strip()
    suite = suite.resolve()
    if target.is_relative_to(suite) or suite.is_relative_to(target):
        raise ValueError("Target and suite must be disjoint directories")
    initialize_suite(suite)
    return {"target": str(target), "source_revision": revision, "suite": str(suite),
            "source_dirty": bool(git(target, "status", "--porcelain").stdout)}


def prepare_bundle(bundle, suite):
    bundle = bundle.resolve(strict=True)
    if not bundle.is_file():
        raise ValueError("Bundle must be a regular file")
    with bundle.open("rb") as artifact:
        digest = hashlib.file_digest(artifact, "sha256").hexdigest()
    suite = suite.resolve()
    initialize_suite(suite)
    return {"bundle": str(bundle), "bundle_sha256": digest, "suite": str(suite)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, help="Fingerprint a supplied Evidence bundle without a target checkout")
    parser.add_argument("target_or_suite", type=Path, metavar="TARGET_OR_SUITE")
    parser.add_argument("suite", type=Path, nargs="?")
    args = parser.parse_args()
    if (args.bundle is None) == (args.suite is None):
        parser.error("use TARGET SUITE or --bundle BUNDLE SUITE")
    try:
        result = (
            prepare_bundle(args.bundle, args.target_or_suite)
            if args.bundle is not None
            else prepare(args.target_or_suite, args.suite)
        )
        print(json.dumps(result))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{error}\n")
