# Agentic Workbench — Agent Instructions (`AGENTS.md`)

Este repositório contém o catálogo canônico de skills de engenharia assistida por IA (`skills/`) e sua documentação arquitetural (`docs/`).

## 1. Princípios de Operação

- **Auto-suficiência das Skills:** Cada skill em `skills/<nome>/SKILL.md` deve ser auto-contida, leve, objetiva e independente de provedor. Não adicione dependências em orquestradores externos removidos nem metadados proprietários.
- **Contexto do Projeto:** Consulte `.project-mapper/graph.sqlite` com a CLI compatível em modo `--offline` quando disponível. Se o mapa ou a CLI estiver ausente, ilegível ou incompleto, siga `docs/README.md` e seu índice; consulte as fontes e os padrões relevantes em qualquer caso.
- **Estilo e Postura (Plugins Terceiros):**
  - **Caveman:** Respostas diretas, sem cerimônia ou *fluff*, preservando toda substância técnica.
  - **Ponytail:** Menor diff funcional que resolve o problema completo (YAGNI estrito).
  - **Codebase Memory MCP:** Prefira ferramentas de grafo (`search_graph`, `trace_path`, `get_code_snippet`, `check_index_coverage`) antes de `grep`/busca bruta.

## 2. Pipeline Core de Engenharia

Quando executar tarefas de desenvolvimento de software usando as skills deste repositório:

1. **Descoberta (Opcional):** Use `skills/brainstorming/SKILL.md` ou `skills/pbb-design/SKILL.md` para clarificar escopo aberto.
2. **Planejamento:** Use `skills/new-scope/SKILL.md` para registrar a especificação e `skills/qa-scope/SKILL.md` em modo `plan` para as evidências de aceitação. New Scope gera `SCOPE.md` de `context.sqlite`; sem esse banco, QA Scope pode criar um escopo independente. Reconcilie as revisões e publique a projeção de tarefas para Execute Scope.
3. **Construção:** Use `skills/execute-scope/SKILL.md` para consultar o contexto do projeto, verificar RED antes de GREEN e executar as verificações de evidência planejadas.
4. **Validação:** Use `skills/qa-scope/SKILL.md` em modo `check` para julgar as evidências do candidato contra `qa.json`. Use `skills/the-grumpy-tech-lead/SKILL.md` para revisão arquitetural independente.
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

- A Execute Scope pode implementar, criar verificações ou rodar procedimentos existentes. Em modo direto, apresenta o plano antes de escrever ou causar efeitos no ambiente. Em modo planejado, mapeia `evidence_checks` às obrigações de `qa.json.contract` e registra observações e falhas em `tasks.json`.
