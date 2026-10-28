# CLAUDE.md — Agentic Workbench

Guia de contexto e instruções operacionais para o Claude Code neste repositório.

## Visão Geral

O **Agentic Workbench** mantém uma coleção enxuta de 14 skills auto-contidas em `skills/<nome>/SKILL.md` para engenharia de software assistida por IA, cobrindo desde descoberta de produto até especificação tripartite, TDD, QA adversarial e memória arquitetural.

## Estrutura do Repositório

- `skills/` — Skills canônicas independentes de provedor (`scope-refinement`, `tdd-orchestrator`, `adversarial-qa`, `project-memory`, `the-grumpy-tech-lead`, `brainstorming`, `pbb-design`, `prompt-generator`, `read-ui-prototype`, `codebase-memory`, `contextual-mentorship`, `ask-antigravity`, `ask-codex`, `ask-opencode`).
- `docs/` — Memória arquitetural do repositório (`README.md`, `.digest.md`, `.graph.json`, `adr/ARCHITECTURE.md`, `adr/TESTS.md`).
- `scripts/` — Scripts de limpeza e sincronização (`cleanup.ps1`, `cleanup.sh`, `sync_skills.py`).

## Diretrizes de Edição

1. **Orientação Rápida:** Leia `docs/.digest.md` antes de explorar arquivos manualmente.
2. **Skills Leves e Auto-contidas:** Ao editar qualquer `skills/<nome>/SKILL.md`, mantenha instruções diretas, verificáveis e sem acoplamento a orquestradores externos.
3. **Isolamento Maker-Checker:** Preserve a separação estrita entre quem especifica (`scope-refinement`), quem implementa (`tdd-orchestrator`) e quem audita (`adversarial-qa`, `the-grumpy-tech-lead`).
4. **Plugins Integrados:** Respeite as diretrizes do **Caveman** (respostas concisas, zero *fluff*), **Ponytail** (menor mudança completa, YAGNI) e **Codebase Memory MCP** (consultas de grafo antes de grep).

## Comandos Úteis

```bash
# Sincronizar skills para os 4 coding agents (Antigravity, Codex, OpenCode, Claude)
python scripts/sync_skills.py
python scripts/sync_skills.py --dry-run
python scripts/sync_skills.py --skill <nome-da-skill>

# Regenerar grafo de documentos em docs/.graph.json
python skills/project-memory/scripts/generate_docs_graph.py docs

# Validar frontmatter e ontologia de docs/
python skills/project-memory/scripts/validate_ontology.py docs
```
