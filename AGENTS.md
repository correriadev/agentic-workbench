# Agentic Workbench — Agent Instructions (`AGENTS.md`)

Este repositório contém o catálogo canônico de skills de engenharia assistida por IA (`skills/`) e sua documentação arquitetural (`docs/`).

## 1. Princípios de Operação

- **Auto-suficiência das Skills:** Cada skill em `skills/<nome>/SKILL.md` deve ser auto-contida, leve, objetiva e independente de provedor. Não adicione dependências em orquestradores externos removidos nem metadados proprietários.
- **Docs-First Orientation:** Antes de modificar a estrutura do repositório ou skills de documentação, leia `docs/.digest.md`, `docs/adr/ARCHITECTURE.md` e `docs/adr/TESTS.md`.
- **Estilo e Postura (Plugins Terceiros):**
  - **Caveman:** Respostas diretas, sem cerimônia ou *fluff*, preservando toda substância técnica.
  - **Ponytail:** Menor diff funcional que resolve o problema completo (YAGNI estrito).
  - **Codebase Memory MCP:** Prefira ferramentas de grafo (`search_graph`, `trace_path`, `get_code_snippet`, `check_index_coverage`) antes de `grep`/busca bruta.

## 2. Pipeline Core de Engenharia

Quando executar tarefas de desenvolvimento de software usando as skills deste repositório:

1. **Descoberta (Opcional):** Use `skills/brainstorming/SKILL.md` ou `skills/pbb-design/SKILL.md` para clarificar escopo aberto.
2. **Especificação Tripartite:** Use `skills/scope-refinement/SKILL.md` para inspecionar `docs/` e código-fonte e gerar `docs/specs/<change_id>/{SCOPE.md, tasks.json, qa.json}`.
3. **Construção (Maker):** Use `skills/tdd-orchestrator/SKILL.md` para implementar o DAG de `tasks.json` via Red-Green-Refactor estrito.
4. **Verificação Independente (Checker):** Use `skills/adversarial-qa/SKILL.md` para validar invariantes e segurança em `qa.json`, e `skills/the-grumpy-tech-lead/SKILL.md` para revisão socrática de impactos sistêmicos.
5. **Memória do Projeto:** Use `skills/project-memory/SKILL.md` para sincronizar `docs/` (`.digest.md`, `.graph.json`, ADRs).

## 3. Comandos de Verificação do Repositório

```powershell
# Regenerar grafo de documentação (project-memory)
python skills/project-memory/scripts/generate_docs_graph.py docs

# Validar ontologia e documentos em docs/
python skills/project-memory/scripts/validate_ontology.py docs
```

## 4. Sincronização de Skills para Coding Agents

Quando o usuário solicitar instalar, atualizar ou propagar skills para seus ambientes locais (Antigravity, Codex, OpenCode ou Claude), utilize o script dedicado:

```powershell
# Simular alterações sem modificar o disco
python scripts/sync_skills.py --dry-run

# Sincronizar todas as skills canônicas para todos os 4 ambientes
python scripts/sync_skills.py

# Sincronizar apenas uma skill específica
python scripts/sync_skills.py --skill <nome-da-skill>

# Sincronizar para um agente específico (ex: antigravity, codex, opencode, claude)
python scripts/sync_skills.py --target <agente>
```

Não use git hooks automáticos para deploy de skills; a sincronização deve ser sempre uma ação intencional.
