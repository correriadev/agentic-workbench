# Evidências e protocolo da investigação

Complemento de [INVESTIGACAO.md](INVESTIGACAO.md); não altera a skill.

## 1. Evidência e limites

**D** = demonstrado por implementação; **R** = reproduzido; **H** = hipótese pendente. Foram lidos SKILL.md, as cinco referências, os cinco scripts, consumidores locais e configuração de CI. O CBM retornou `project not found or not indexed` para este checkout; a exploração usou leitura e `rg`. Não se inferiu ausência a partir do grafo.

O grafo documental local contém somente dois ADRs; não há `docs/feature/`. Portanto, este checkout demonstra contratos de consumidores, não eficácia em um monorepo de produto. Não foram investigados outros projetos pessoais. Fixtures isoladas estabeleceram limites mecânicos; não representam produção nem desempenho de agentes.

Fontes, relativas à raiz `ai-dev-environment`:

- [S — SKILL.md](../../../skills/authored/project-memory/SKILL.md): PRECONDITIONS, TOTAL CONTEXT BUDGET, Steps 8–10.
- [O — ONTOLOGY-RULES.md](../../../skills/authored/project-memory/references/ONTOLOGY-RULES.md): STORAGE AND OWNERSHIP, SCOPE AND EXTRACTION, STATUS AND RECONCILIATION.
- [G — generate_docs_graph.py](../../../skills/authored/project-memory/scripts/generate_docs_graph.py): `parse_markdown_file`, `validate_feature_micrograph`, `build_docs_graph`, `main`.
- [V — validate_ontology.py](../../../skills/authored/project-memory/scripts/validate_ontology.py): `Validator.__init__`, `load`, `check_claim`, `validate`.
- [T — tdd-orchestrator](../../../skills/authored/tdd-orchestrator/SKILL.md): Feature micrograph routing.
- [F — scope-refinement](../../../skills/authored/scope-refinement/SKILL.md): Shared Project Orientation.
- [A — autonomous-orchestrator](../../../skills/authored/autonomous-orchestrator/SKILL.md): E2.
- [I — verify_repository.py](../../../scripts/verify_repository.py): `verify`; [CI](../../../.github/workflows/validate.yml).


## 4. Comparação executada

[experimento.py](experimento.py) reproduz probes e comparação; [resultados.json](resultados.json) registra ambiente, tempos individuais, contagens e SHA-256 dos arquivos da skill. Hashes permaneceram iguais. Comando, na raiz do projeto: `python -B docs/specs/otimizacao_project_memory/experimento.py`.

Candidata mínima: para edição editorial com projeção de roteamento anterior conhecida e igual à atual, reutilizar o grafo e validar o alvo. Baseline reconstrói/publica o grafo e valida o mesmo alvo. Igualdade dos resultados foi assertada. Três repetições por tamanho, ordem alternada, Python 3.12.10/Windows, cache de disco não controlado; documentos sintéticos pequenos, sem claims no ensaio de escala.

| Documentos | Leituras atual/candidata | Caracteres lidos atual/candidata | Mediana ms atual/candidata |
|---:|---:|---:|---:|
| 10 | 12 / 4 | 5.271 / 3.970 | 14,74 / 4,03 |
| 100 | 102 / 4 | 48.741 / 32.410 | 116,73 / 26,49 |
| 500 | 502 / 4 | 241.941 / 158.810 | 558,80 / 124,24 |

Com 500 documentos, intervalos: 558,20–572,99 ms e 123,66–126,77 ms. Grafo: 79.044 caracteres. Ambas fizeram 500 verificações de arquivos por repetição; candidata leu o índice duas vezes. Publicações do grafo: três versus zero. Portanto, reduz parsing e escrita, mas não torna custo independente de N.

Não foram medidos tokens de modelo, acurácia de agentes, tempo humano, memória residente, sincronização de digest/README ou custo de construir a projeção anterior. Caracteres são I/O Python, não tokens enviados ao modelo. Os probes demonstram rejeições ausentes; não medem prevalência de respostas erradas. A candidata cobre somente manutenção editorial, não o SDLC completo.


## 7. Evolução e avaliação

1. Reparar fixtures/caminhos e incluir suíte na CI. Alinhar A/E2 com evidências externas e exclusões. Preservar schema e atualizar hashes de distribuição em `profiles/assets.sha256.json` após revisão.
2. Pilotar política de leitura e sincronização condicional em T/F e project-memory. Preservar formatos e fallbacks; rollback é voltar ao rebuild completo. Troca de dono exige reconciliar todos os IDs qualificados antes de remover origem.
3. Adicionar detecção de afetados e publicação segura somente após testes de renome, exclusão, interrupção e dois escritores. Sem dados confiáveis, fallback explícito. Cache reverso fica condicionado ao perfil de custo.
4. Comparar baseline/candidata em casos pareados, mesma revisão, ferramentas, orçamento e modelo. Contrabalançar ordem, repetir e registrar dispersão. Não estabelecer ganho percentual arbitrário.

| Cenário | Oráculo independente da memória e evidência esperada |
|---|---|
| Nova feature | Inspeção prévia de padrão e registro; teste deve detectar omissão do registro. |
| Bug entre camadas | Reprodução falhando, causa no fluxo real e regressão passando nas fronteiras afetadas. |
| Contrato compartilhado | Lista de consumidores obtida do código/contratos antes da recuperação; incompatibilidades avaliadas. |
| Seleção de testes | Relação comportamento/asserts inspecionada; separar recomendação, execução e relatório de cobertura. |
| Renome/exclusão | Diff preparado previamente; locators reconciliados, IDs preservados e referências não resolvidas explicitadas. |
| Memória stale/conflitante | Código, requisito e execução congelados antes do ensaio; preservar divergência e impedir uso como fato atual. |

Descoberta recebe capacidades/lacunas; refinamento recebe requisitos e conflitos; planejamento recebe fronteiras e dependentes; implementação recebe padrões/registros/testes; revisão recebe diff, invariantes e execuções; testes recebem comportamentos e asserts; diagnóstico recebe reprodução, configuração e cadeia causal. Cada etapa devolve evidência e incerteza, não toda a documentação.

Aceitação: nenhuma omissão material ou afirmação sem suporte nos casos com oráculo; caminhos/IDs válidos; nenhuma promoção editorial a fato; recuperação e geração completa equivalentes onde aplicável; interrupção recuperável e concorrência sem perda silenciosa. Medir correção por caso, recall de evidências necessárias, falsos positivos, uso stale, arquivos únicos/releituras, tokens reais, tempo e trabalho de manutenção. Crescer documentos, rotas, cadeias e pacotes mantendo a tarefa; registrar custo frio/quente. Congelar oráculos por inspeção separada antes de comparar; geração de memória não pode ser sua própria resposta correta. Qualidade e custo em produção continuam pendentes.

## Mapa detalhado do fluxo atual

| Etapa | Comportamento demonstrado |
|---|---|
| Entrada | S aceita caminho direto; caso contrário usa digest, tags e um salto. Detecta stack, verifica/cria baselines e consulta hints de projetos. |
| Leitura | O já exige fluxo representativo, falhas, contratos, dependências e parada por respostas ou lacunas. T seleciona feature, `must_read`, opcionais e micrografo; RED começa pelos testes, GREEN por entradas/registros/padrões. |
| Extração | O já distingue capacidade/regra/contrato/decisão, requisito/observação/hipótese, IDs canônicos, evidências e incerteza. Não falta ontologia. |
| Persistência | Agente escreve Markdown e `graph.knowledge`; scripts não extraem significado. `document_graph.graph_block` lê um bloco e rejeita duplicações de bloco/chaves. |
| Índices | G lê integralmente todos os Markdown de adr/feature, verifica rotas, deduplica/ordena arestas e escreve `.graph.json`. Não gera digest nem README. Preserva `related_projects`, sem confirmar sua autoridade. |
| Recuperação | F prepara `${orientation}` uma vez e reaproveita entre fases. T tem fallback quando rotas faltam. Não há mecanismo executável de seleção semântica nestes scripts. |
| Invalidação | O manda reexaminar claims afetadas e dependentes; snapshots são opcionais. V valida formato/referências, não conteúdo, snapshots ou resultados de testes. |


## Verificação da entrega

`verify_repository.py` também foi executado. Além do tamanho do primeiro rascunho (corrigido), apontou 23 fontes de skills ausentes e divergência de `profiles/assets.sha256.json`. Não houve correção desses problemas fora do escopo. A investigação preservou os hashes dos arquivos de project-memory. O resultado global não deve ser apresentado como aprovação do repositório.
