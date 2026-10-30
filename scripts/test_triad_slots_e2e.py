#!/usr/bin/env python3
"""
End-to-End Verification Test for the TDD Triad Git Slot Protocol
Validates:
1. Slot provisioning under .worktrees/slots/<change_id>/ (maker-slot, qa-slot)
2. Exclude registration in <git-common-dir>/info/exclude (root status stays clean)
3. Maker atomic commit in maker-slot detached at base_oid
4. Blast-radius inspection on candidate_oid
5. QA slot positioning, overlay injection, and harness archive
6. Clean fast-forward merge (--ff-only) into main worktree
7. Interrupted-run crash recovery: reset --hard & clean -fd restoring slot
8. Safe worktree removal and pruning
"""

import os
import pathlib
import shutil
import subprocess
import tempfile
import sys

def run_git(cwd, *args, check=True):
    res = subprocess.run(
        ["git"] + list(args),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    if check and res.returncode != 0:
        raise RuntimeError(
            f"Git command failed: git {' '.join(args)}\n"
            f"CWD: {cwd}\n"
            f"Exit: {res.returncode}\n"
            f"STDOUT: {res.stdout}\n"
            f"STDERR: {res.stderr}"
        )
    return res

def test_triad_e2e():
    temp_dir = tempfile.mkdtemp(prefix="triad-e2e-")
    print(f"[TEST] Working in temporary directory: {temp_dir}")
    try:
        repo_root = pathlib.Path(temp_dir) / "repo"
        repo_root.mkdir()

        # Step 0: Initialize repository with an initial commit
        print("[STEP 0] Initializing Git repository...")
        run_git(repo_root, "init", "--initial-branch=main")
        run_git(repo_root, "config", "user.name", "Triad Test")
        run_git(repo_root, "config", "user.email", "triad-test@example.com")
        
        # Initial commit on main
        readme = repo_root / "README.md"
        readme.write_text("# Project\nInitial base.\n", encoding="utf-8")
        run_git(repo_root, "add", "README.md")
        run_git(repo_root, "commit", "-m", "chore: initial commit")
        base_oid = run_git(repo_root, "rev-parse", "HEAD").stdout.strip()
        print(f"  -> Base OID: {base_oid}")

        # Step 1: Resolve common-dir and register .worktrees/ in info/exclude
        print("\n[STEP 1] Testing exclude registration and slot provisioning...")
        common_dir = pathlib.Path(run_git(repo_root, "rev-parse", "--git-common-dir").stdout.strip())
        if not common_dir.is_absolute():
            common_dir = (repo_root / common_dir).resolve()
        
        exclude_file = common_dir / "info" / "exclude"
        exclude_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Register .worktrees/ if not present
        existing_exclude = exclude_file.read_text(encoding="utf-8") if exclude_file.exists() else ""
        if ".worktrees/" not in existing_exclude:
            with open(exclude_file, "a", encoding="utf-8") as f:
                f.write(".worktrees/\n")
        
        assert ".worktrees/" in exclude_file.read_text(encoding="utf-8"), "Exclude registration failed!"
        print("  -> .worktrees/ registered in info/exclude")

        # Provision persistent slots
        change_id = "change-42"
        slots_dir = repo_root / ".worktrees" / "slots" / change_id
        maker_slot = slots_dir / "maker-slot"
        qa_slot = slots_dir / "qa-slot"
        harnesses_dir = slots_dir / "qa-harnesses"
        harnesses_dir.mkdir(parents=True, exist_ok=True)

        run_git(repo_root, "worktree", "add", "--detach", str(maker_slot), base_oid)
        run_git(repo_root, "worktree", "add", "--detach", str(qa_slot), base_oid)

        # Invariant checks
        status_root = run_git(repo_root, "status", "--porcelain").stdout.strip()
        assert status_root == "", f"Root checkout is dirty after slot creation!\n{status_root}"
        print("  -> Main repository status is 100% clean (untracked .worktrees/ correctly excluded)")

        maker_head = run_git(maker_slot, "rev-parse", "HEAD").stdout.strip()
        qa_head = run_git(qa_slot, "rev-parse", "HEAD").stdout.strip()
        assert maker_head == base_oid, f"Maker slot HEAD mismatch: {maker_head} != {base_oid}"
        assert qa_head == base_oid, f"QA slot HEAD mismatch: {qa_head} != {base_oid}"

        sym_maker = run_git(maker_slot, "symbolic-ref", "-q", "HEAD", check=False)
        assert sym_maker.returncode != 0, "Maker slot must be in detached HEAD state!"
        print("  -> maker-slot and qa-slot created in detached HEAD at base_oid")

        # Step 2: Maker execution in maker-slot
        print("\n[STEP 2] Simulating tdd-maker RED-GREEN-REFACTOR inside maker-slot...")
        pkg_dir = maker_slot / "src"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        feat_file = pkg_dir / "calculator.py"
        feat_file.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

        test_dir = maker_slot / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "test_calculator.py"
        test_file.write_text("from src.calculator import add\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8")

        # Maker stages and commits
        run_git(maker_slot, "add", "src/calculator.py", "tests/test_calculator.py")
        run_git(maker_slot, "commit", "-m", "feat(T1): implement add function")
        candidate_oid = run_git(maker_slot, "rev-parse", "HEAD").stdout.strip()
        assert candidate_oid != base_oid, "Candidate commit was not created!"
        print(f"  -> Candidate commit produced: {candidate_oid}")

        # Pin candidate ref in supervisor namespace
        candidate_ref = f"refs/triad/candidates/{change_id}/B1-1"
        run_git(repo_root, "update-ref", candidate_ref, candidate_oid)
        assert run_git(repo_root, "rev-parse", candidate_ref).stdout.strip() == candidate_oid
        print(f"  -> Candidate ref pinned: {candidate_ref}")

        # Step 3: Blast-Radius Confinement Audit
        print("\n[STEP 3] Auditing blast-radius of candidate commit...")
        diff_tree = run_git(repo_root, "diff-tree", "--no-commit-id", "--name-status", "-r", candidate_oid).stdout
        print(f"  -> Diff-tree:\n{diff_tree.strip()}")
        allowed_files = {"src/calculator.py", "tests/test_calculator.py"}
        for line in diff_tree.strip().splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                action, path = parts[0], parts[1]
                assert path in allowed_files, f"Out-of-scope file detected: {path}"
        print("  -> Blast radius verified: 100% within files_allowed")

        # Step 4: QA positioning & overlay verification in qa-slot
        print("\n[STEP 4] Simulating adversarial-qa verification in qa-slot...")
        run_git(qa_slot, "switch", "--detach", candidate_oid)
        assert run_git(qa_slot, "rev-parse", "HEAD").stdout.strip() == candidate_oid
        
        # Inject QA overlay
        harness = qa_slot / "tests" / "test_adversarial.py"
        harness.write_text("from src.calculator import add\ndef test_edge():\n    assert add(0, 0) == 0\n", encoding="utf-8")
        
        # Archive harness to persistent directory
        shutil.copy2(harness, harnesses_dir / "test_adversarial.py")
        assert (harnesses_dir / "test_adversarial.py").exists()
        print("  -> QA harness archived to persistent slots directory")

        # Clean overlay from qa-slot
        harness.unlink()
        run_git(qa_slot, "reset", "--hard", candidate_oid)
        qa_status = run_git(qa_slot, "status", "--porcelain").stdout.strip()
        assert qa_status == "", f"qa-slot remains dirty after overlay cleanup:\n{qa_status}"
        print("  -> qa-slot overlay cleaned; qa-slot returns clean verdict PASS")

        # Step 5: Fast-forward integration into main repository
        print("\n[STEP 5] Integrating candidate via git merge --ff-only...")
        run_git(repo_root, "merge", "--ff-only", candidate_oid)
        new_main_oid = run_git(repo_root, "rev-parse", "HEAD").stdout.strip()
        assert new_main_oid == candidate_oid, "Main branch failed to fast-forward to candidate OID!"
        assert (repo_root / "src" / "calculator.py").exists(), "Integrated files missing in main worktree!"
        print(f"  -> Main worktree successfully advanced to {new_main_oid}")

        # Step 6: Interrupted Slot Recovery (The bug report scenario)
        print("\n[STEP 6] Testing interrupted batch crash recovery in maker-slot...")
        # Simulate worker crash leaving untracked and incomplete files
        dirty_file1 = maker_slot / "src" / "incomplete.py"
        dirty_file1.write_text("def half_baked():", encoding="utf-8")
        dirty_file2 = maker_slot / "tests" / "incomplete.test.py"
        dirty_file2.write_text("import incomplete", encoding="utf-8")

        assert run_git(maker_slot, "status", "--porcelain").stdout.strip() != "", "Setup failed: slot should be dirty!"
        print("  -> Injected dirty untracked files into maker-slot (simulating interrupted run)")

        # Orchestrator recovery protocol: git reset --hard <oid> and git clean -fd
        run_git(maker_slot, "reset", "--hard", candidate_oid)
        run_git(maker_slot, "clean", "-fd")

        recovered_status = run_git(maker_slot, "status", "--porcelain").stdout.strip()
        assert recovered_status == "", f"Recovery failed: slot is still dirty:\n{recovered_status}"
        assert not dirty_file1.exists(), "Dirty file 1 was not cleaned!"
        assert not dirty_file2.exists(), "Dirty file 2 was not cleaned!"
        print("  -> Recovery protocol restored maker-slot to 100% clean state")

        # Step 7: Teardown and Prune
        print("\n[STEP 7] Tearing down slots and pruning worktrees...")
        run_git(repo_root, "worktree", "remove", "--force", str(maker_slot))
        run_git(repo_root, "worktree", "remove", "--force", str(qa_slot))
        run_git(repo_root, "worktree", "prune")

        wt_list = run_git(repo_root, "worktree", "list").stdout.strip()
        print(f"  -> Remaining worktrees:\n{wt_list}")
        assert str(maker_slot) not in wt_list, "maker-slot was not pruned!"
        assert str(qa_slot) not in wt_list, "qa-slot was not pruned!"
        print("  -> Worktrees cleanly pruned from Git metadata")

        print("\n=======================================================")
        print(">>> ALL 7 END-TO-END VERIFICATION CHECKS PASSED 100% <<<")
        print("=======================================================")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    success = test_triad_e2e()
    sys.exit(0 if success else 1)
