# Agentic Workbench

Repositório enxuto de engenharia de software assistida por IA. Centraliza skills auto-contidas, leves e independentes de provedor para descoberta de produto, especificação tripartite baseada em evidências, construção via TDD, auditoria adversarial de QA e memória arquitetural.

---

## 1. Plugins e Ferramentas de Terceiros

O ecossistema opera integrado aos seguintes plugins e servidores MCP:

| Componente | Papel no Fluxo |
|---|---|
| **Caveman** | Comunicação ultraconcisa (*smart caveman*). Elimina cerimônia e *fluff*, reduzindo o consumo de tokens de saída mantendo 100% do rigor técnico. |
| **Ponytail** | Modo *Lazy Senior Dev*. Aplica YAGNI estrito, prioriza o menor diff funcional que resolve a causa raiz e rastreia atalhos conscientes via `shortcut:`. |
| **Codebase Memory MCP** | Grafo de conhecimento estrutural do código (AST). Substitui buscas textuais caras por `search_graph`, `trace_path`, `detect_changes` e queries Cypher. |
| **Open Graph MCP** | Governança de alterações em repositório, isolamento por *changesets* e coordenação de *locks* entre agentes. |
| **RTK (Rust Token Killer)** | Proxy de linha de comando que comprime saídas verbosas de terminal (`git`, `test`, `build`) antes do envio ao contexto do LLM. |

---

## 2. Skills Mais Importantes (Pipeline Core)

O fluxo principal de engenharia separa **Intenção (Humano)**, **Construção (Maker / TDD)** e **Verificação (Checker / QA)**:

```text
[brainstorming / pbb-design]
            ↓
   [scope-refinement]  ──► gera docs/specs/<change_id>/{SCOPE.md, tasks.json, qa.json}
            ↓
   [tdd-orchestrator]  ──► executa Red-Green-Refactor no DAG de tasks.json
            ↓
    [adversarial-qa]   ──► valida invariantes, bordas, concorrência e segurança (qa.json)
            ↓
[the-grumpy-tech-lead] ──► revisão socrática de impactos sistêmicos e arquitetura
            ↓
    [project-memory]   ──► atualiza docs/ (.digest.md, .graph.json, ADRs)
```

### Catálogo de Skills (`skills/`)

#### Engenharia Core
- **`scope-refinement`**: Traduz intenção de negócio e inspeção do código (`docs/` + código-fonte) em uma especificação tripartite atômica (`SCOPE.md`, `tasks.json`, `qa.json`).
- **`tdd-orchestrator`**: Executa ciclos autônomos de TDD (Red-Green-Refactor) respeitando a topologia do DAG em `tasks.json`, confinamento de *blast-radius* (`files_allowed`) e loop de retrabalho com QA.
- **`adversarial-qa`**: Juiz independente de QA. Executa testes destrutivos, de fronteira, concorrência, propriedades e segurança contra `qa.json`, sem reutilizar mocks do TDD.
- **`the-grumpy-tech-lead`**: Tech Lead revisor focado em impactos sistêmicos (queries N+1, *memory leaks*, *race conditions*, quebra de contratos de camadas) via perguntas socráticas baseadas em evidências (`arquivo:linha`).
- **`project-memory`**: Cria e mantém documentação estruturada em `docs/` (`README.md`, `adr/ARCHITECTURE.md`, `adr/TESTS.md`, `.digest.md`, `.graph.json`) para orientação rápida de agentes.

#### Produto, Design e Descoberta
- **`brainstorming`**: Exploração colaborativa de problemas, restrições e alternativas arquiteturais antes de escrever código.
- **`pbb-design`**: Avaliação crítica de produto (Product CTO/PM), corte implacável de escopo, calibração epistêmica e estruturação de Product Backlog rastreável via PBB (*Problema → Expectativa → Persona → Funcionalidade → PBI*).
- **`prompt-generator`**: Engenharia reversa e geração estruturada de meta-prompts, personas e system instructions para LLMs.
- **`read-ui-prototype`**: Analisa protótipos visuais (telas, imagens, Figma) e gera especificação estrutural e semântica de frontend sem inventar valores visuais (HEX/px).

#### Navegação, Mentoria e Delegação CLI
- **`codebase-memory`**: Guia operacional para exploração arquitetural e análise de impacto usando o servidor `codebase-memory-mcp`.
- **`contextual-mentorship`**: Mentoria técnica contextual focada em progressão causal e tomada de decisão.
- **`ask-antigravity` / `ask-codex` / `ask-opencode`**: Wrappers transparentes para delegar consultas, *second-opinion reviews* ou implementações em *git worktrees* isolados para CLIs locais.

---

## 3. Arquitetura de Pastas

```text
agentic-workbench/
├── docs/
│   ├── .digest.md              # Resumo de orientação rápida para agentes
│   ├── .graph.json             # Grafo de documentos do repositório
│   ├── README.md               # Índice navegável da documentação
│   └── adr/
│       ├── ARCHITECTURE.md     # Arquitetura e limites das skills
│       └── TESTS.md            # Estratégia e comandos de verificação
├── scripts/
│   ├── cleanup.ps1             # Higienização estrutural do repositório (PowerShell)
│   ├── cleanup.sh              # Higienização estrutural do repositório (Bash)
│   └── sync_skills.py          # Sincronização e espelhamento intencional para coding agents
├── skills/                     # 14 skills auto-contidas (1 pasta por skill com SKILL.md)
│   ├── adversarial-qa/
│   ├── ask-antigravity/
│   ├── ask-codex/
│   ├── ask-opencode/
│   ├── brainstorming/
│   ├── codebase-memory/
│   ├── contextual-mentorship/
│   ├── pbb-design/
│   ├── project-memory/
│   ├── prompt-generator/
│   ├── read-ui-prototype/
│   ├── scope-refinement/
│   ├── tdd-orchestrator/
│   └── the-grumpy-tech-lead/
├── AGENTS.md                   # Regras operacionais para agentes (Codex, Antigravity, OpenCode)
├── CLAUDE.md                   # Regras operacionais equivalentes para Claude Code
└── README.md                   # Este documento
```

---

## 4. Sincronização de Skills entre Coding Agents

A distribuição de skills para os ambientes de execução locais é **intencional e sob demanda** através de `scripts/sync_skills.py` (sem hooks automáticos em git commit para prevenir quebras acidentais durante desenvolvimento).

### Ambientes Atendidos:
- **Google Antigravity:** `~/.gemini/config/skills/`
- **OpenAI Codex:** `~/.codex/skills/`
- **OpenCode:** `~/.config/opencode/skills/`
- **Claude Code:** `~/.claude/skills/`

### Comandos de Sincronização:

```bash
# Simular mudanças em todos os agentes (dry-run seguro)
python scripts/sync_skills.py --dry-run

# Sincronizar todas as skills canônicas para todos os 4 agentes
python scripts/sync_skills.py

# Sincronizar apenas uma skill específica (ex: nova ou alterada)
python scripts/sync_skills.py --skill prompt-generator

# Sincronizar para apenas um agente específico
python scripts/sync_skills.py --target claude
python scripts/sync_skills.py --target codex
python scripts/sync_skills.py --target antigravity
python scripts/sync_skills.py --target opencode
```

O script realiza **espelhamento completo de diretórios** (`shutil.rmtree` + `shutil.copytree`), garantindo zero resíduos órfãos, e purga automaticamente skills obsoletas.

