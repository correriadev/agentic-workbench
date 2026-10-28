#!/usr/bin/env python3
"""
Sincronizador intencional e controlado de skills para Coding Agents:
- Google Antigravity (~/.gemini/config/skills)
- OpenAI Codex (~/.codex/skills)
- OpenCode (~/.config/opencode/skills)
- Claude Code (~/.claude/skills)

Garante espelhamento completo de diretórios (sem resíduos) e purga de skills obsoletas.
"""

import argparse
import os
import pathlib
import shutil
import sys

ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
REPO_SKILLS = ROOT_DIR / "skills"
HOME = pathlib.Path.home()

TARGETS = {
    "antigravity": HOME / ".gemini" / "config" / "skills",
    "codex": HOME / ".codex" / "skills",
    "opencode": HOME / ".config" / "opencode" / "skills",
    "claude": HOME / ".claude" / "skills"
}

OBSOLETE_SKILLS = {
    # Skills do antigo ecossistema CBM/Harness
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
    "union-tracer",
    # Snapshots Jev legados
    "jev-browser-use",
    "jev-compaction",
    "jev-computer-use",
    "jev-frontier-work",
    "jev-mailbox",
    "jev-memory",
    "jev-model-routing",
    "jev-search",
    "jev-setup",
    "jev-skill-select",
    "jev-social-research"
}


def get_available_skills():
    if not REPO_SKILLS.exists():
        return []
    return sorted([d.name for d in REPO_SKILLS.iterdir() if d.is_dir() and (d / "SKILL.md").exists()])


def sync_single_skill(src_dir: pathlib.Path, dst_dir: pathlib.Path, dry_run: bool = False):
    existed = dst_dir.exists()
    action = "Substituir (mirror)" if existed else "Criar"
    if dry_run:
        return action
    if existed:
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)
    return action


def main():
    parser = argparse.ArgumentParser(description="Sincronizador canônico de skills para coding agents.")
    parser.add_argument("--dry-run", action="store_true", help="Simula as ações sem modificar o disco.")
    parser.add_argument("--skill", type=str, default=None, help="Sincroniza apenas uma skill específica.")
    parser.add_argument("--target", choices=["all", "antigravity", "codex", "opencode", "claude"], default="all",
                        help="Limita a sincronização a um agente específico.")
    parser.add_argument("--no-prune", action="store_true", help="Não remove skills obsoletas dos destinos.")
    args = parser.parse_args()

    available_skills = get_available_skills()
    if not available_skills:
        print(f"Erro: Nenhuma skill válida encontrada em {REPO_SKILLS}", file=sys.stderr)
        sys.exit(1)

    if args.skill:
        if args.skill not in available_skills:
            print(f"Erro: Skill '{args.skill}' não encontrada no repositório. Disponíveis:", file=sys.stderr)
            for s in available_skills:
                print(f"  - {s}", file=sys.stderr)
            sys.exit(1)
        skills_to_sync = [args.skill]
    else:
        skills_to_sync = available_skills

    targets_to_process = TARGETS if args.target == "all" else {args.target: TARGETS[args.target]}

    mode_label = "[DRY-RUN] " if args.dry_run else ""
    print(f"===========================================================")
    print(f"{mode_label}SINCRONIZAÇÃO DE SKILLS ({len(skills_to_sync)} canônica(s))")
    print(f"===========================================================")

    for target_name, target_dir in targets_to_process.items():
        print(f"\n-> Destino: {target_name.upper()} ({target_dir})")
        if not target_dir.exists():
            if args.dry_run:
                print(f"   [!] Diretório será criado: {target_dir}")
            else:
                target_dir.mkdir(parents=True, exist_ok=True)

        # 1. Prune de skills obsoletas
        if not args.no_prune and target_dir.exists():
            for item in target_dir.iterdir():
                if item.is_dir() and item.name in OBSOLETE_SKILLS:
                    if args.dry_run:
                        print(f"   [-] [PRUNE] Removerá obsoleta: {item.name}")
                    else:
                        shutil.rmtree(item)
                        print(f"   [-] [PRUNED] Removida obsoleta: {item.name}")

        # 2. Espelhamento de skills selecionadas
        for skill_name in skills_to_sync:
            src = REPO_SKILLS / skill_name
            dst = target_dir / skill_name
            action = sync_single_skill(src, dst, dry_run=args.dry_run)
            prefix = "[PLAN] " if args.dry_run else "[OK]   "
            print(f"   {prefix}{action}: {skill_name}")

    print("\n===========================================================")
    if args.dry_run:
        print("Dry-run concluído. Nenhuma alteração foi realizada no disco.")
    else:
        print("Sincronização concluída com sucesso em todos os alvos selecionados.")
    print("===========================================================")


if __name__ == "__main__":
    main()
