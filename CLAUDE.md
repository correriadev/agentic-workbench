# CLAUDE.md — Agentic Workbench

Guia de contexto e instruções operacionais para o Claude Code neste repositório.

## Visão Geral

O **Agentic Workbench** mantém uma coleção enxuta de skills auto-contidas em `skills/<nome>/SKILL.md` para engenharia de software assistida por IA, cobrindo desde descoberta de produto até planejamento modular, TDD, validação de evidências e memória arquitetural.

## Estrutura do Repositório

- `skills/` — Skills canônicas independentes de provedor (`new-scope`, `execute-scope`, `qa-scope`, `project-memory`, `the-grumpy-tech-lead`, `brainstorming`, `pbb-design`, `prompt-generator`, `read-ui-prototype`, `codebase-memory`, `contextual-mentorship`, `ask-antigravity`, `ask-codex`, `ask-opencode`).
- `docs/` — Memória arquitetural do repositório (`README.md`, `.digest.md`, `.graph.json`, `adr/ARCHITECTURE.md`, `adr/TESTS.md`).
- `scripts/` — Scripts de limpeza e sincronização (`cleanup.ps1`, `cleanup.sh`, `sync_skills.py`).

## Diretrizes de Edição

1. **Orientação Rápida:** Consulte o mapa `.project-mapper/graph.sqlite` em modo `--offline` quando disponível; caso contrário, siga `docs/README.md` e seu índice. Confira fontes e padrões relevantes em qualquer caso.
2. **Skills Leves e Auto-contidas:** Ao editar qualquer `skills/<nome>/SKILL.md`, mantenha instruções diretas, verificáveis e sem acoplamento a orquestradores externos.
3. **Planejamento, construção e validação:** `new-scope` e `qa-scope plan` podem iniciar o `SCOPE.md` e produzir seus planos em qualquer ordem. `execute-scope` executa RED → GREEN e produz as evidências previstas. `qa-scope check` julga essas evidências contra `qa.json`.
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

- Em modo direto, a Execute Scope pode implementar, criar verificações ou rodar cenários existentes. Apresenta ação, alvo, pré-condições, efeitos e verificação antes de escrever ou causar efeitos. Em modo planejado, registra evidências por obrigação e candidato em `tasks.json`.
