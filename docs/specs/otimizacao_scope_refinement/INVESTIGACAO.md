# Scope-refinement: escopo de mudança baseado em evidências

Investigação em 28/10/2026, sem alterar skills. Recomendação: substituir a sequência DDD obrigatória por refinamento de uma mudança verificável, usando entrada do usuário/PBB, memória selecionada de `docs` e inspeção dirigida. DDD continua útil quando linguagem, invariantes ou fronteiras precisam ser descobertas; tamanho de contexto, sozinho, não torna DDD obsoleto.

O problema demonstrado é reconstruir modelos e transportar decisões por vários documentos em toda tarefa. A proposta aproveita a [investigação de project-memory](../otimizacao_project_memory/INVESTIGACAO.md), cujas melhorias ainda não estão implementadas. Fontes, linhas, medidas e limites: [EVIDENCIAS_E_AVALIACAO.md](EVIDENCIAS_E_AVALIACAO.md). Exemplo concreto: [EXEMPLO_ESCOPO.md](EXEMPLO_ESCOPO.md).

## 1. Diagnóstico priorizado

**P1 — A intenção perde estrutura no handoff.** O CTO manda transmitir PBB, premissas e perguntas. O orquestrador A2 define `${scope}` como título + descrição do backlog, mas a tabela/modelo não tem coluna `Description`. Não existe mapeamento explícito de IDs de PBI, fonte ou status de premissa. A projeção contratual reproduzida perde esses campos; não foi executado um agente para provar perda em todos os runtimes.

**P1 — Planejamento completo não significa pronto.** A3 avança por existência de `004`; o teste isolado aceitou arquivos vazios. A skill anuncia sucesso por documentos gerados, sem vínculo obrigatório à revisão atual, aceites cobertos ou perguntas bloqueantes. Há validação sintática instruída, mas não scripts ou testes próprios no diretório da skill.

**P1 — Rigor fixo antes de conhecer o tamanho da mudança.** São quatro fases sequenciais e `2 + 2P` arquivos para P projetos. Event Storming, 10–15 termos e 3–5 decisões são exigidos mesmo quando a memória já contém as respostas. O design tático já proíbe forçar DDD e respeita a arquitetura existente; o defeito é a obrigatoriedade da descoberta estratégica e dos inventários, não ausência dessa adaptação.

**P1 — Derivação fechada pode propagar uma omissão.** O agente 04 manda derivar somente do design tático, embora outra regra permita contrato existente. Cenários viram fonte do RED. Uma regra omitida em 003 pode desaparecer de 004 e dos testes. QA adversarial e rework são salvaguardas reais; não se pode afirmar que toda a esteira ignora evidência independente. O risco é detectar tarde uma lacuna que deveria bloquear o escopo.

**P2 — Decomposição por camada dificulta entrega vertical.** O agente 03 ordena tipos, agregados, serviços e persistência; frontend começa por estilos. Obriga 2–4 itens de escopo e 1–3 aceites, e dependência única `string|null`. Um próprio exemplo tem um item. Isso não representa diretamente uma tarefa dependente de dois projetos; serializar artificialmente muda o plano. Raízes distintas chamadas `service` também colidem como identidade.

**P2 — Validade e expansão incompletas.** Já existe `${orientation}` compartilhada, fallback e checagem de paths. Existência não prova atualidade. Após entrevista, só se reavaliam opcionais dos nós já selecionados: uma nova capacidade pode exigir novas sementes. O limite de oito perguntas encerra a entrevista, não demonstra resolução. A proibição geral de ler outros specs impede reutilizar um contrato anterior indicado pelo usuário, se aplicada literalmente.

**P2 — Contratos textuais frágeis.** A4 depende do heading exato `## Section 6 — Ordered Development Tasks`. Seu fallback JSON usa a primeira e última chave, inadequadas a arrays de várias tarefas sem fence. Foi reproduzido o algoritmo descrito; não há parser executável correspondente demonstrado neste checkout.

## 2. Fluxo recomendado

```mermaid
flowchart LR
    U[Usuário ou PBI selecionado] --> R[Recuperar docs e conferir evidências]
    R --> S[Delimitar mudança e aceites]
    S --> P[Fatiar por resultado e risco]
    P --> V[Validar prontidão do escopo]
    V --> T[Implementar e testar]
    T --> Q[Revisar com evidência independente]
    Q --> M[Reconciliar project-memory]
    M --> R
```

PBB responde por problema, pessoa, valor e prioridade; scope-refinement traduz somente o PBI selecionado em mudança executável. `project-memory` mantém conhecimento durável, incluindo intenção e observação separadas. Código/CBM dão estrutura e impacto; execução fornece resultados. Specs de mudança preservam proposta e histórico, sem se tornarem automaticamente fatos atuais.

### Entrada e autoridade

Receber pedido original ou referência ao PBI, ID/fonte, resultado esperado, fronteiras, restrições, premissas e perguntas com autoria/status. Receber projetos com IDs estáveis e raízes explícitas; usar identificador de mudança separado de domínio. Não refazer PBB válido. Para correção/refactor bem delimitado, aceitar entrada técnica direta; descoberta de produto segue PBB quando necessária.

Preservar requisito autorizado, observação do código e hipótese como coisas distintas. Uma resposta humana define intenção, não altera retroativamente o comportamento observado. Modelo pode decidir detalhe técnico reversível dentro do escopo autorizado; não transforma premissa de negócio em requisito aprovado.

### Seleção, expansão e parada

1. Usar caminho explícito; senão digest/grafo para encontrar capacidades. Ler claims, evidências e rotas relevantes, mantendo IDs e estados. Não carregar `docs` inteira nem recriar mapa global.
2. Formular obrigações: o que muda, o que deve continuar, quem consome, onde provar. Reabrir fontes mutáveis relevantes antes de usar uma claim como fundamento; quando faltarem docs, inspecionar código dirigido e registrar lacuna, sem gerar documentação global como pré-condição.
3. Expandir para callers/consumidores em alteração de contrato; registros em nova extensão; schema/migração em dados; configuração em comportamento dependente de ambiente; testes e fixtures para provar preservação. Usar CBM quando cobertura permitir, com fallback de busca. Código gerado remete ao gerador/schema.
4. Refazer seleção quando usuário/PBB introduzir outra capacidade. Manter orçamento acumulado, evidências já lidas e pendências; reutilizar orientação válida por etapa, sem tratar um salto como fronteira de impacto.
5. Parar quando cada mudança e invariante material tiver aceite verificável, fonte ou lacuna explícita, consumidores avaliados e abordagem de teste. Orçamento esgotado produz escopo parcial/bloqueado, não sucesso fictício.

### Granularidade e risco

Fatiar por resultado demonstrável de ponta a ponta; tarefas internas seguem dependências reais, não ordem universal de camadas. Uma mudança pequena não precisa glossary/context-map. Design adicional só quando houver escolha consequente, contrato compartilhado, migração, segurança, concorrência ou rollout. Registrar opção escolhida e razão; usar ADR existente ou solicitar decisão no fluxo apropriado, sem criar outro catálogo.

Para monorepos, mapear slice a pacotes afetados; para vários projetos, explicitar produtor, consumidores, compatibilidade e ordem de entrega. Dependências são lista de IDs, com detecção de ciclos. Não paralelizar escritores dos mesmos arquivos sem coordenação. Não transformar quantidade de arquivos ou estimativa de horas em regra universal de corte.

## 3. Saída mínima e prontidão

Um `docs/specs/<change-id>/SCOPE.md` canônico por mudança delimitada: objetivo/origem; dentro/fora; estado atual com evidências; delta comportamental; aceites identificados; slices/tarefas; lacunas; validação e rollout aplicáveis. Se exceder o orçamento, dividir a mudança ou extrair detalhe necessário com referência explícita, sem multiplicar arquivos por projeto automaticamente.

Manter dados de execução em um único bloco JSON versionado: identidade/revisão, fontes, aceites, tarefas com `project_id`, `acceptance_ids`, `evidence_ids`, `depends_on[]`, e perguntas bloqueantes. Prosa acrescenta razões; não repete o mesmo inventário. O contrato proposto não altera `graph.knowledge` nem faz o grafo global indexar specs.

Prontidão é derivada: IDs/referências válidos, dependências resolvidas, fontes relevantes reexaminadas, todos os aceites materiais ligados a prova planejada e nenhum bloqueio na slice escolhida. `draft`, `ready`, `blocked` e `superseded` descrevem o escopo; não são estados de claim. Implementação/revisão continuam no estado do orquestrador. `ready` não significa teste passou nem aprovação de deploy.

Testes nascem de pedido/PBB, contratos existentes e risco observado; design ajuda a escolher nível e localização. Mudanças descobertas no RED/review revisam o escopo afetado com motivo e fonte. Proibir invenção de requisitos continua válido; proibir novos testes fundamentados não.

## 4. Atualização e ligação com project-memory

Registrar base por projeto e locators/hashes das fontes selecionadas. Mudança de HEAD é sinal para verificar diff relevante, não motivo para reler tudo. Renome exige reconciliar locator; exclusão exige lacuna; mudança de contrato exige rever consumidores e aceites. Edição editorial não renova prova. Retomada confere identidade, versão e fontes; arquivo existente não basta.

Após implementação, revisão e evidência de execução, entregar à project-memory somente claims/contratos/decisões afetados, paths antigos/novos, resultados e incerteza. Registrar observação do que foi comprovado; proposta recusada permanece histórico. Não importar backlog, tasks ou spec inteira para memória. Publicação da memória segue seu contrato atual; otimizações da investigação anterior exigem implementação separada.

## 5. Alternativas atuais

| Alternativa | Avaliação |
|---|---|
| DDD atual com fases opcionais | Menor migração inicial; insuficiente se mantiver perda de proveniência e gate por existência. |
| Spec Kit completo | Guia brownfield recomenda próxima mudança delimitada, reutilizando arquitetura, sem especificar retroativamente todo o sistema. Útil como referência; adoção integral cria outra estrutura e contratos. [Guia oficial](https://github.com/github/spec-kit/blob/main/docs/guides/existing-projects.md). |
| OpenSpec completo | Separa comportamento durável de deltas por mudança e permite rigor progressivo. Boa correspondência conceitual; manter sua memória paralela a project-memory duplicaria autoridade. [Conceitos oficiais](https://raw.githubusercontent.com/Fission-AI/OpenSpec/main/docs/concepts.md). |
| Fluxo local por delta e evidência | Recomendado: incorporar princípios acima, preservar ferramentas e reduzir contrato obrigatório. Eficiência ainda precisa de avaliação em tarefas. |

DORA sustenta pequenos lotes e feedback rápido; não prova que um template específico de escopo seja superior. Usar essa orientação para slices verificáveis, não como justificativa para mais artefatos. [Fonte primária](https://dora.dev/capabilities/working-in-small-batches/).

## 6. Evolução, compatibilidade e decisão

1. Corrigir handoff PBB e gate de prontidão mantendo 003/004. Preservar autoria/status; adicionar probes de contrato à CI. Remover cotas e permitir omitir descoberta DDD quando a memória responde ao problema.
2. Introduzir `SCOPE.md` em piloto e leitores versionados em autonomous-orchestrator, TDD, QA e tech lead. Atualizar agentes Codex/OpenCode, CTO/software-architect e E2 de memória. Preservar suites e hashes de distribuição. Não remover 001/002 enquanto consumidores ainda os exigirem.
3. Durante transição, gerar 003/004 somente como projeções da fonte canônica, com revisão identificada e sem edição dupla. Projeção de DAG para dependência única deve recusar perda de informação; esses casos exigem leitor novo. Não prometer compatibilidade automática.
4. Migrar estado sem duplicar tarefas na retomada; preservar IDs e registrar mudança de revisão. Encerrar projeções quando os consumidores forem testados. Rollback conserva modo legado por mudança; não sobrescreve histórico nem mistura formatos silenciosamente.

**Manter:** PBB, orientação compartilhada, incerteza, arquitetura existente, aceites observáveis, revisão independente. **Alterar:** handoff, decomposição, evidência, invalidação e prontidão. **Remover como obrigação:** Event Storming/glossário/context-map, quotas, design de todos os tipos e ordem fixa de camadas. **Adiar:** instalação de frameworks, novo índice/banco, agentes adicionais e automação extensa sem medição.

O experimento comprovou limites de contratos, não superioridade de uma execução por LLM. Aceitar evolução apenas se casos pareados preservarem requisitos/proveniência, recuperarem evidências materiais e retomarem sem usar escopo stale; medir tokens, tempo e manutenção além de qualidade. O [anexo](EVIDENCIAS_E_AVALIACAO.md) define amostra, oráculos e critérios.
