#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

echo "Iniciando simplificacao estrutural em: $ROOT_DIR"

if [ -d "skills/authored" ]; then
  for s in autonomous-orchestrator memory-context horizon-deliberator integrar-temenos level-graduator; do
    if [ -e "skills/authored/$s" ]; then
      git rm -rf "skills/authored/$s" 2>/dev/null || true
      rm -rf "skills/authored/$s" 2>/dev/null || true
    fi
  done

  for dir in skills/authored/*; do
    [ -d "$dir" ] || continue
    name="$(basename "$dir")"
    if [ ! -e "skills/$name" ]; then
      echo "Movendo skill para raiz de skills/: $name"
      git mv "$dir" "skills/$name" 2>/dev/null || mv "$dir" "skills/$name"
    fi
  done
  rm -rf "skills/authored"
fi

PATHS_TO_REMOVE=(
  "skills/autonomous-orchestrator"
  "skills/memory-context"
  "skills/horizon-deliberator"
  "skills/integrar-temenos"
  "skills/level-graduator"
  "skills/curated"
  ".work"
  "integrations"
  "mcp"
  "profiles"
  "tests"
  "tools"
  "docs/research"
  "docs/specs"
  "docs/ARCHITECTURE.md"
  "docs/CUSTOMIZATION.md"
  "docs/INSTALL.md"
  "docs/INVENTORY.md"
  "docs/RECOVERY.md"
  "docs/SECURITY.md"
  "environment.yaml"
  "environment.lock.yaml"
  "scripts/acceptance.py"
  "scripts/bootstrap.ps1"
  "scripts/bootstrap.sh"
  "scripts/check_mcp.py"
  "scripts/environment.py"
  "scripts/verify_repository.py"
  "scripts/__pycache__"
)

for rel_path in "${PATHS_TO_REMOVE[@]}"; do
  if [ -e "$rel_path" ]; then
    echo "Removendo: $rel_path"
    git rm -rf "$rel_path" 2>/dev/null || true
    rm -rf "$rel_path" 2>/dev/null || true
    echo "Removido: $rel_path"
  fi
done

echo "Simplificacao concluida com sucesso."
