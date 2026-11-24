# Agentic Workbench

> Catálogo canônico de skills e protocolos de engenharia de software para coding agents locais (**Google Antigravity**, **OpenAI Codex**, **OpenCode** e **Claude Code**).

O Workbench oferece skills independentes para planejar a mudança, construir com testes e julgar a evidência de entrega.

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

### Construção e validação

`blueprint` registra a especificação em `context.sqlite` e gera o resumo `SCOPE.md`. Sua projeção versionada é publicada para execução como `tasks.json`. `quality-gate plan` registra obrigações de evidência em `qa.json` e também pode usar um escopo independente quando não há banco do Blueprint. Reconcilie as obrigações e as revisões antes da execução.

`forge` executa as tarefas na working tree, começa pelos testes unitários em RED e só então implementa em GREEN. Também executa as verificações planejadas para produzir evidências. Quando houver contrato de QA, `quality-gate check` julga a evidência vinculada ao candidato e registra o veredito.

### Pesquisa Aprofundada e Meta-Engenharia
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
| [`the-grumpy-tech-lead`](skills/the-grumpy-tech-lead/SKILL.md) | Revisor socrático; audita vazamentos de recursos, queries N+1, contratos e integridade de design. |
| [`project-memory`](skills/project-memory/SKILL.md) | Mantém a memória documental em `docs/` (`.digest.md`, `.graph.json`, ADRs). |
| [`blueprint`](skills/blueprint/SKILL.md) | Planeja a alteração em SQLite, gera o resumo e projeta tarefas para o Forge. |
| [`quality-gate`](skills/quality-gate/SKILL.md) | Define as obrigações de evidência em `plan` e avalia o candidato em `check`. |
| [`journey-verifier`](skills/journey-verifier/SKILL.md) | Gera um repositório E2E separado, executa a jornada contra o alvo real e registra efeitos observados por canais independentes. |
| [`forge`](skills/forge/SKILL.md) | Implementa mudanças, cria verificações e executa procedimentos existentes, incluindo E2E. |

### 💡 Produto, Design & Pesquisa
| Skill | Papel |
|---|---|
| [`brainstorming`](skills/brainstorming/SKILL.md) | Exploração conceitual, restrições e alternativas antes da escrita de código. |
| [`experiment-design`](skills/experiment-design/SKILL.md) | Desenha experimentos para apoiar decisões e interpreta as evidências de comparações. |
| [`pbb-design`](skills/pbb-design/SKILL.md) | Product Backlog Building; alinhamento de problemas, expectativas, personas e PBIs. |
| [`read-ui-prototype`](skills/read-ui-prototype/SKILL.md) | Extrai especificações semânticas e acessíveis a partir de protótipos de tela e imagens. |
| [`researcher`](skills/researcher/SKILL.md) | Orquestração de pesquisa profunda em árvore macro-to-micro com síntese em `docs/research/`. |
| [`prompt-generator`](skills/prompt-generator/SKILL.md) | Geração estruturada de meta-prompts, personas e instruções de sistema para LLMs. |
| [`skill-creator`](skills/skill-creator/SKILL.md) | Criação, auditoria e otimização de novas skills com padrões rigorosos de token economy. |

### 🧭 Navegação, Mentoria & Delegação CLI
| Skill | Papel |
|---|---|
| [`codebase-memory`](skills/codebase-memory/SKILL.md) | Exploração estrutural do código via Knowledge Graph (AST) com o servidor MCP. |
| [`project-mapper`](skills/project-mapper/SKILL.md) | Agentes investigam o repositório e publicam descobertas em JSON livre, com relações e evidências por trecho. A consulta em SQLite permite localizar uma descoberta, abri-la e seguir suas ligações. |
| [`contextual-mentorship`](skills/contextual-mentorship/SKILL.md) | Sessões de mentoria técnica guiada, reflexão e aprendizado colaborativo. |
| [`outcome-delegation`](skills/outcome-delegation/SKILL.md) | Briefs verificáveis para delegação e avaliação de resultados contra o contrato original. |
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
python scripts/sync_skills.py --skill blueprint

# Sincronizar uma skill para um único agente
python scripts/sync_skills.py --skill forge --target codex

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
├── scripts/
│   ├── cleanup.ps1 / cleanup.sh    # Scripts de higienização do workspace
│   └── sync_skills.py              # Sincronizador canônico para os 4 coding agents
├── skills/                         # Catálogo de skills autocontidas
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

### Forge em modo direto ou planejado

- **Direto.** A Forge pode implementar uma mudança, criar uma verificação ou executar um cenário existente. Após a inspeção somente leitura, apresenta na sessão a ação, o alvo, as pré-condições, os efeitos previstos e a verificação antes da primeira escrita ou de uma execução com efeitos. RED → GREEN se aplica a mudanças de comportamento do produto. Esse modo dispensa os três contratos.
- **Planejado.** Indique o plano ou o `change_id`. Em `docs/specs/<change_id>/`, `context.sqlite` guarda a especificação, `SCOPE.md` é seu resumo, `tasks.json` guarda a projeção, os estados e as evidências, e `qa.json` guarda as obrigações e os vereditos. Quando houver QA formal, use `quality-gate plan`, reconcilie as tarefas com `blueprint`, publique a projeção com `forge` e avalie com `quality-gate check`. Contratos inválidos devem ser reconciliados antes da execução.

Para E2E, a Forge segue o runbook e reutiliza o runner do projeto. Confere o ambiente e a versão servida, executa o cenário e registra as observações ou os bloqueios. No modo planejado, associa cada `evidence_check` de `tasks.json` às obrigações de `qa.json.contract` e registra a evidência por obrigação e candidato, incluindo falhas observadas. Uma suíte verde com observações faltantes deixa uma lacuna. O veredito cabe a `quality-gate check`. Quando disponível, Blueprint e Forge consultam o grafo do Project Mapper como apoio à investigação e conferem as fontes atuais.

Os scripts `contract.py` acompanham as skills e validam as gravações. A revisão de QA identifica o conteúdo de `qa.json.contract`. Registrar um veredito preserva essa revisão.
