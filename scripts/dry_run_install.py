import os
import sys
import json
import pathlib
import difflib

REPO_SKILLS = pathlib.Path(r"C:\Users\User\Documents\agentic-workbench\skills")

TARGETS = {
    "codex": pathlib.Path(r"C:\Users\User\.codex\skills"),
    "opencode": pathlib.Path(r"C:\Users\User\.config\opencode\skills"),
    "antigravity": pathlib.Path(r"C:\Users\User\.gemini\config\skills")
}

def analyze():
    canonical = sorted([d.name for d in REPO_SKILLS.iterdir() if d.is_dir()])
    print(f"CANONICAL SKILLS IN WORKBENCH ({len(canonical)}):")
    for s in canonical:
        print(f"  - {s}")
    print()

    report = {}

    for target_key, target_dir in TARGETS.items():
        print(f"==================================================")
        print(f"TARGET: {target_key} -> {target_dir}")
        print(f"==================================================")
        if not target_dir.exists():
            print(f"Diretório não existe! Será criado: {target_dir}")
            existing = []
        else:
            existing = sorted([d.name for d in target_dir.iterdir() if d.is_dir() and d.name != ".system"])

        to_create = [s for s in canonical if s not in existing]
        to_replace = [s for s in canonical if s in existing]
        orphans = [s for s in existing if s not in canonical]

        print(f"A CRIAR ({len(to_create)}):")
        for s in to_create:
            print(f"  + {s}")

        print(f"\nA SUBSTITUIR COMPLETAMENTE ({len(to_replace)}):")
        for s in to_replace:
            # Check file differences
            src_files = set(p.relative_to(REPO_SKILLS / s).as_posix() for p in (REPO_SKILLS / s).rglob("*") if p.is_file())
            dst_files = set(p.relative_to(target_dir / s).as_posix() for p in (target_dir / s).rglob("*") if p.is_file())
            extra_in_dst = dst_files - src_files
            missing_in_dst = src_files - dst_files
            note = ""
            if extra_in_dst:
                note += f" [remove {len(extra_in_dst)} resíduos antigos]"
            if missing_in_dst:
                note += f" [adiciona {len(missing_in_dst)} novos arquivos]"
            print(f"  ~ {s}{note}")

        print(f"\nÓRFÃOS / LEGADOS NO DESTINO ({len(orphans)}):")
        for s in orphans:
            # Check for similar names
            close = difflib.get_close_matches(s, canonical, n=2, cutoff=0.5)
            similarity = f" (semelhante a: {', '.join(close)})" if close else ""
            print(f"  ? {s}{similarity}")

        print()

if __name__ == "__main__":
    analyze()
