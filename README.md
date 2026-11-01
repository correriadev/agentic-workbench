# Agentic Workbench

> Catálogo canônico de skills e protocolos de engenharia de software para coding agents locais (**Google Antigravity**, **OpenAI Codex**, **OpenCode** e **Claude Code**).

O repositório fornece um ecossistema modular e desacoplado onde skills operam com responsabilidades atômicas: quem especifica não implementa, quem implementa não testa, e quem audita atua de forma adversarial e independente.

---

## Sumário Rápido

1. [Início Rápido (Quickstart)](#1-início-rápido-quickstart)
2. [Fluxos de Trabalho Recomendados](#2-fluxos-de-trabalho-recomendados)
3. [Catálogo Canônico de Skills](#3-catálogo-canônico-de-skills)
4. [Plugins e Ferramentas Complementares](#4-plugins-e-ferramentas-complementares)
5. [Sincronização entre Coding Agents](#5-sincronização-entre-coding-agents)
6. [Estrutura do Repositório e Documentação](#6-estrutura-do-repositório-e-documentação)

---

## 1. Início Rápido (Quickstart)

### Passo 1: Clone o repositório
```bash
git clone https://github.com/seu-usuario/agentic-workbench.git
cd agentic-workbench
```

### Passo 2: Sincronize as skills para seus agentes instalados
A distribuição para os diretórios locais dos agentes é intencional e controlada via `scripts/sync_skills.py`:

```bash
# Simulação segura (não altera arquivos)
python scripts/sync_skills.py --dry-run

# Sincronizar todas as skills para todos os 4 agentes locais
python scripts/sync_skills.py

# Ou sincronizar apenas para o seu agente em uso:
python scripts/sync_skills.py --target antigravity   # ~/.gemini/config/skills
python scripts/sync_skills.py --target codex         # ~/.codex/skills
python scripts/sync_skills.py --target claude        # ~/.claude/skills
python scripts/sync_skills.py --target opencode      # ~/.config/opencode/skills
```

### Passo 3: Use as skills diretamente nos agentes
Uma vez sincronizadas, invoque as skills em qualquer projeto pelo nome ou objetivo no chat do seu agente.

---

## 2. Fluxos de Trabalho Recomendados

Escolha o fluxo ideal conforme o nível de rigor e o estágio da tarefa:

### Fluxo A: Produção & Engenharia Rigorosa (TDD Triad)
*Para funcionalidades críticas, refatorações de arquitetura e código de produção.*

```text
[brainstorming / pbb-design]
             ↓
    [scope-refinement]  ──► gera docs/specs/<id>/{SCOPE.md, tasks.json, qa.json}
             ↓
    [tdd-orchestrator]  ──► coordena lotes e slots git desacoplados
        ├── [tdd-maker] ──► ciclo RED-GREEN-REFACTOR em maker-slot (sem ver qa.json)
        └── [adversarial-qa] ──► suite destrutiva em qa-slot (pass/fail objetivo)
             ↓
  [the-grumpy-tech-lead] ──► auditoria socrática (impactos de escala, N+1, leaks)
             ↓
      [project-memory]  ──► atualiza docs/ (.digest.md, .graph.json, ADRs)
```

### Fluxo B: Prototipagem Ultrarrápida (Zero Git / Fast Path)
*Para MVPs, scripts rápidos, validação de conceitos e spikes sem cerimônia de git.*

```text
[fast-scope] ──► gera plano enxuto docs/specs/<id>/{SCOPE.md, tasks.json} (sem qa.json)
      ↓
 [fast-code] ──► executa DAG diretamente na working tree, sem worktrees e sem git
```

### Fluxo C: Pesquisa Aprofundada & Meta-Engenharia
*Para investigar tópicos complexos ou criar/auditar novas skills.*

```text
[researcher]     ──► decompõe tópicos em shards macro/micro e consolida em docs/research/
[skill-creator]  ──► cria, audita e otimiza skills com economia de tokens e prompt caching
```

---

## 3. Catálogo Canônico de Skills

Todas as skills ficam isoladas em `skills/<nome>/` e contêm sua especificação canônica em `SKILL.md`.

### 🛠️ Engenharia Core & TDD
| Skill | Papel |
|---|---|
| [`scope-refinement`](skills/scope-refinement/SKILL.md) | Especificação tripartite atômica baseada em evidências (`SCOPE.md`, `tasks.json`, `qa.json`). |
| [`tdd-orchestrator`](skills/tdd-orchestrator/SKILL.md) | Orquestrador do DAG; despacha lotes, gerencia branches de trabalho e integra commits aprovados. |
| [`tdd-maker`](skills/tdd-maker/SKILL.md) | Construtor RED-GREEN-REFACTOR estrito restrito a `files_allowed`. Não acessa o arquivo de QA. |
| [`adversarial-qa`](skills/adversarial-qa/SKILL.md) | Juiz independente; executa testes destrutivos, limites, concorrência e segurança contra `qa.json`. |
| [`the-grumpy-tech-lead`](skills/the-grumpy-tech-lead/SKILL.md) | Revisor socrático; audita vazamentos de recursos, queries N+1, contratos e integridade de design. |
| [`triad-mediator`](skills/triad-mediator/SKILL.md) | Árbitro forense read-only chamado apenas quando o triad trava em impasse (`blocked`). |
| [`project-memory`](skills/project-memory/SKILL.md) | Mantém a memória documental em `docs/` (`.digest.md`, `.graph.json`, ADRs). |

### ⚡ Prototipagem Rápida
| Skill | Papel |
|---|---|
| [`fast-scope`](skills/fast-scope/SKILL.md) | Especificação bipartite ágil (`SCOPE.md`, `tasks.json`) sem overhead de QA formal. |
| [`fast-code`](skills/fast-code/SKILL.md) | Executor direto na working tree local, focado em velocidade (zero worktree / zero commits intermediários). |

### 💡 Produto, Design & Pesquisa
| Skill | Papel |
|---|---|
| [`brainstorming`](skills/brainstorming/SKILL.md) | Exploração conceitual, restrições e alternativas antes da escrita de código. |
| [`pbb-design`](skills/pbb-design/SKILL.md) | Product Backlog Building; alinhamento de problemas, expectativas, personas e PBIs. |
| [`read-ui-prototype`](skills/read-ui-prototype/SKILL.md) | Extrai especificações semânticas e acessíveis a partir de protótipos de tela e imagens. |
| [`researcher`](skills/researcher/SKILL.md) | Orquestração de pesquisa profunda em árvore macro-to-micro com síntese em `docs/research/`. |
| [`prompt-generator`](skills/prompt-generator/SKILL.md) | Geração estruturada de meta-prompts, personas e instruções de sistema para LLMs. |
| [`skill-creator`](skills/skill-creator/SKILL.md) | Criação, auditoria e otimização de novas skills com padrões rigorosos de token economy. |

### 🧭 Navegação, Mentoria & Delegação CLI
| Skill | Papel |
|---|---|
| [`codebase-memory`](skills/codebase-memory/SKILL.md) | Exploração estrutural do código via Knowledge Graph (AST) com o servidor MCP. |
| [`contextual-mentorship`](skills/contextual-mentorship/SKILL.md) | Sessões de mentoria técnica guiada, reflexão e aprendizado colaborativo. |
| [`ask-antigravity`](skills/ask-antigravity/SKILL.md) | Delega tarefas e revisões para a CLI local do Google Antigravity (`agy`). |
| [`ask-codex`](skills/ask-codex/SKILL.md) | Delega tarefas e revisões isoladas para a CLI local do OpenAI Codex. |
| [`ask-opencode`](skills/ask-opencode/SKILL.md) | Delega tarefas e pareceres técnicos para a CLI local do OpenCode. |
| [`ask-claude`](skills/ask-claude/SKILL.md) | Delega tarefas, consultas e revisões para a CLI local do Anthropic Claude. |

---

## 4. Plugins e Ferramentas Complementares

| Ferramenta / Plugin | Benefício Principal |
|---|---|
| **Caveman** | Elimina cerimônia e conversa fiada; foca em respostas técnicas diretas e economiza tokens de saída. |
| **Ponytail** | Filosofia *Lazy Senior Dev*: resolve problemas com a menor alteração segura possível (YAGNI estrito). |
| **Codebase Memory MCP** | Grafo AST para consultas estruturais (`search_graph`, `trace_path`), dispensando buscas cegas via grep. |
| **Open Graph MCP** | Governança de concorrência e mudanças com changesets e locks transacionais entre agentes. |
| **RTK (Rust Token Killer)** | Comprime saídas ruidosas de terminal (`git diff`, builds, logs) antes de consumirem a janela de contexto. |

---

## 5. Sincronização entre Coding Agents

O script [`scripts/sync_skills.py`](scripts/sync_skills.py) gerencia a distribuição das skills:

```bash
# Sincronizar apenas uma skill específica
python scripts/sync_skills.py --skill scope-refinement

# Sincronizar uma skill para um único agente
python scripts/sync_skills.py --skill fast-code --target codex

# Limpeza e higienização de arquivos residuais
python scripts/sync_skills.py --dry-run
```

- **Espelhamento Limpo:** Remove arquivos órfãos nos diretórios de destino via `shutil.rmtree` + `shutil.copytree`.
- **Purga de Skills Obsoletas:** Remove automaticamente pastas antigas descontinuadas.

---

## 6. Estrutura do Repositório e Documentação

```text
agentic-workbench/
├── docs/                           # Documentação e memória do repositório
│   ├── .digest.md                  # Orientação de leitura rápida para IAs (< 60 linhas)
│   ├── .graph.json                 # Grafo de relacionamentos entre documentos
│   ├── README.md                   # Índice geral navegável da documentação
│   └── adr/
│       ├── ARCHITECTURE.md         # Arquitetura modular e regras de dependência
│       ├── TESTS.md                # Protocolo de testes e validações
│       └── TDD_TRIAD_BLUEPRINT.md  # Blueprint para reprodução externa da Tríade TDD
├── scripts/
│   ├── cleanup.ps1 / cleanup.sh    # Scripts de higienização do workspace
│   └── sync_skills.py              # Sincronizador canônico para os 4 coding agents
├── skills/                         # Catálogo de 21 skills autocontidas
├── AGENTS.md                       # Regras operacionais para Antigravity, Codex e OpenCode
├── CLAUDE.md                       # Regras operacionais específicas para Claude Code
└── README.md                       # Este documento
```

### Comandos de Validação da Documentação
```powershell
# Regenerar o grafo de documentos
python skills/project-memory/scripts/generate_docs_graph.py docs

# Validar conformidade de ontologia e links
python skills/project-memory/scripts/validate_ontology.py docs
```
