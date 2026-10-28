import os
import shutil
import pathlib

REPO_SKILLS = pathlib.Path(r"C:\Users\User\Documents\agentic-workbench\skills")

CANONICAL_SKILLS = sorted([d.name for d in REPO_SKILLS.iterdir() if d.is_dir()])

TARGETS = {
    "codex": pathlib.Path(r"C:\Users\User\.codex\skills"),
    "opencode": pathlib.Path(r"C:\Users\User\.config\opencode\skills"),
    "antigravity": pathlib.Path(r"C:\Users\User\.gemini\config\skills")
}

OBSOLETE_SKILLS = {
    "autonomous-orchestrator",
    "memory-context",
    "horizon-deliberator",
    "integrar-temenos",
    "level-graduator",
    "harness-evaluator",
    "harness-tracer",
    "meta-harness",
    "qa-orchestrator",
    "adversarial-traverser",
    "constellation-individuator",
    "dialogo-sombra",
    "graph-grounding",
    "refusal-discipline",
    "skill-contract-attestor",
    "temenos",
    "union-tracer"
}

def sync_skill(src_dir: pathlib.Path, dst_dir: pathlib.Path):
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)

def main():
    print(f"Iniciando sincronização de {len(CANONICAL_SKILLS)} skills...")

    for name, target_dir in TARGETS.items():
        print(f"\n==========================================")
        print(f"PROCESSANDO TARGET: {name} -> {target_dir}")
        print(f"==========================================")

        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. Limpeza de skills obsoletas
        for item in target_dir.iterdir():
            if item.is_dir() and item.name in OBSOLETE_SKILLS:
                print(f"  [-] Removendo skill obsoleta: {item.name}")
                shutil.rmtree(item)

        # 2. Instalação e espelhamento das skills canônicas
        # No caso do plugin harness-kit, instalamos apenas as skills de harness ou todas?
        # Para evitar divergência, instalamos todas as canônicas
        for skill_name in CANONICAL_SKILLS:
            src = REPO_SKILLS / skill_name
            dst = target_dir / skill_name
            existed = dst.exists()
            sync_skill(src, dst)
            action = "Substituído (mirror)" if existed else "Criado"
            print(f"  [+] {action}: {skill_name}")

    print("\n==========================================")
    print("VERIFICAÇÃO FINAL:")
    print("==========================================")
    for name, target_dir in TARGETS.items():
        installed = sorted([d.name for d in target_dir.iterdir() if d.is_dir() and d.name != ".system"])
        print(f"{name} ({len(installed)} skills):")
        print(f"  {', '.join(installed)}")

if __name__ == "__main__":
    main()
