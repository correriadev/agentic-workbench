# Evolução de project-memory para o SDLC

Investigação de 28/10/2026. Recomendação: preservar o modelo atual; tornar sincronização condicional e recuperação orientada à pergunta e ao diff. Antes de ampliar a arquitetura, corrigir a suíte e alinhar consumidores. Nenhuma alteração na skill. Fontes e protocolo estão no [anexo de evidências](EVIDENCIAS_E_AVALIACAO.md).


## 1. Fluxo e contratos

A tarefa entra por caminho direto ou digest/tags/um salto. O agente inspeciona fluxos e evidências, extrai claims e escreve Markdown. G reconstrói o grafo; V verifica estrutura. T/F recuperam micrografos e orientação compartilhada. A invalidação factual depende do agente. 

Preservar `nodes`, `edges`, `related_projects`, `related_docs.must_read/optional`, as cinco listas de rotas, IDs qualificados e `knowledge.schema_version=1`. V rejeita campos extras dentro do conhecimento. A integração real inclui T, F, seus agentes, A/E2 e agentes de revisão que recebem digest. Consumo inspecionado, não executado.

## 2. Diagnóstico priorizado

**P0 — Base de regressão quebrada (R).** `python -B -m unittest discover -s ai-dev-environment/skills/authored/project-memory/scripts -v` executou 43 testes em 0,906 s: 35 passaram, 3 falhas e 5 erros. Sete ocorrências vêm de fixtures sem micrografo obrigatório; a outra procura `skills/skills/tdd-orchestrator/SKILL.md`. Localizadores e execução estão no anexo. A CI só descobre `tests/`; esses testes aninhados não entram naquele comando. Aprovação da CI não prova saúde da skill.

**P1 — Regras conflitantes na integração (D).** A/E2 proíbe qualquer referência fora de adr/feature, exige preservar caminhos anteriores e orienta evitar releitura de fontes. S/O permitem evidência em código/configuração/execução, exigem caminhos existentes e reinspeção de fontes mutáveis. Isso prejudica justamente exclusões e grounding. Falha efetiva de um agente sob essas instruções permanece H.

**P1 — Mudança local paga trabalho global (D/R).** S exige digest por invocação, reconstrução do grafo e reconciliação de README mesmo para alvo único. G percorre todos os documentos e caminhos; V, mesmo com `--document`, lê o índice inteiro e verifica a existência de todos os nós. Uma rota inválida em feature alheia bloqueou a reconstrução da fixture. Atualizar não significa necessariamente produzir diff textual, mas a inspeção global ocorre.

**P1 — Validade depende de execução disciplinada pelo agente (D/R).** Claims contraditórias e evidências renomeadas/excluídas foram aceitas pelos dois scripts. O resultado declara corretamente `evidence_verified: false`: é limite anunciado, não promessa quebrada de verificação factual. V segue referências saindo do alvo; validar A não visitou B, que deriva de A. Não existe descoberta reversa automática de afetados nesses scripts.

**P2 — Limites não limitam contexto acumulado (D/R).** S já manda orçar leitura acumulada, mas não define contador ou orçamento por tarefa. G/V aceitaram documento acima de 10.000 caracteres; I possui uma verificação separada de tamanho para Markdown em docs. O grafo JSON não tem teto. Listas exaustivas exigidas por S competem com claims no bloco único. Splits aumentam navegação; leitura de todos os `must_read` pode continuar crescendo.

**P2 — Publicação e concorrência frágeis (D/H).** G/main escreve diretamente com `open(..., 'w')`; não há troca atômica, lock ou comparação da revisão de entrada. Digest, grafo e README são etapas separadas. Interrupção pode deixar JSON parcial; dois escritores podem publicar visão antiga. O mecanismo está demonstrado; perda real e frequência não foram reproduzidas. JSON em uma linha dificulta merges de mudanças distintas.

**Hipótese “um salto basta”: não confirmada.** T/F começam por um salto, porém S/O já mandam expandir para evidências/dependências. Falta operacionalizar gatilhos e testar omissões; não é correto afirmar que toda execução para no primeiro salto.


## 3. Menor proposta completa

### Seleção, expansão e parada

Entrada: tarefa, etapa SDLC, escopo autorizado, paths/símbolos, diff com base conhecida e resultados existentes. Reutilizar `${orientation}` acrescentando, no contexto transitório, perguntas, evidências lidas, revisão, pendências e custo acumulado; não criar outro documento obrigatório.

Selecionar caminho explícito ou feature por IDs/tags; usar seu micrografo como sementes. Cada leitura deve responder pergunta concreta: regra, integração, impacto ou teste. Expandir quando houver mudança de assinatura/erro/dado para callers e consumidores; registro/export/DI para configuração; estado persistente para schema/migração; falha distribuída para dependências e compensação; teste ausente para suíte/configuração. Cruzar pacotes quando essas fronteiras atravessarem pacotes, não por proximidade de diretório.

Usar CBM para estrutura quando disponível e com cobertura verificada; complementar com busca/inspeção para reflexão, código gerado, configurações e lacunas do índice. Seguir dependências e dependentes até responder a obrigação, com conjunto de visitados; salto não é critério de completude. Ao atingir orçamento de contexto/tempo, devolver lacuna e próximo passo, nunca conclusão negativa.

Parar quando cada pergunta material tiver evidência atual ou lacuna explícita, fronteiras alteradas tiverem consumidores avaliados e testes pertinentes estiverem identificados. Exemplo: adicionar comando exige entrada, registro, implementação representativa e teste de registro; corrigir bug de serialização exige contrato, adapter e consumidores, mesmo fora da feature inicial.

### Registro e atualização

Persistir afirmação consequente dentro da capacidade/contrato que possui autoridade sobre o comportamento. Feature continua sendo contêiner, não precisa coincidir com ticket ou pacote. Contrato compartilhado tem um dono, escolhido pela responsabilidade de manter sua compatibilidade; consumidores usam ID qualificado. Fluxo transversal referencia donos; decisão cita ADR. Registrar invariantes, erros, exceções e justificativas indisponíveis no código. Consultar símbolos e inventários diretamente; resumir navegação, não duplicar implementação.

Para diff, mapear caminhos antigos/novos às evidências e rotas; incluir referências reversas `derived_from` e dependências de contrato como candidatos, não como prova de impacto. Renome preserva IDs e exige resolver locator; exclusão mantém lacuna até decidir substituição. Mudança de fonte torna a claim candidata a `stale`; reexaminar antes de reutilizar. Alteração editorial não renova snapshot nem status. Sem base confiável, validar conservadoramente o escopo e declarar limite.

Começar com revisão Git e hashes de arquivos efetivamente inspecionados usando `snapshot` existente. Hash alterado exige reinspeção; hash igual não valida dependência externa. Execução deve carregar comando, ambiente, revisão e resultado no artefato referenciado. Não misturar “teste relevante”, “teste executado” e “cobertura”: esta requer relatório ligado ao mesmo código e escopo.

Regerar grafo apenas quando mudar projeção documental; README quando mudar navegação; digest quando mudarem suas fontes. Em mudança de código, verificar rotas afetadas mesmo sem mudar grafo. Sem projeção anterior confiável, executar rebuild completo. Publicar com arquivo temporário e substituição atômica; verificar revisão antes de gravar e serializar publicação por projeto. Isso não cria transação multiarquivo: conferir consistência ao final e permitir reconstrução após interrupção.

## 4. Alternativas e decisão

| Opção | Decisão e motivo |
|---|---|
| Markdown + contratos atuais | Manter: auditável, já consumido, sem migração de storage. |
| Simplificar regras e sincronização | Adotar primeiro: resolve custo e conflitos demonstrados. Remover exaustividade de rotas; manter sementes por papel e descoberta por ferramentas. |
| Índice reverso derivado | Adiar até medir varredura de evidências. Se necessário, cache descartável por revisão; jamais segunda autoridade. |
| Hash por símbolo | Adiar: parser e normalização adicionam complexidade. Hash de arquivo é conservador e suficiente para piloto. |
| Banco vetorial/novo grafo/serviço | Adiar: não demonstrada lacuna de recall lexical que justifique operação adicional; não resolve validade. |
| CBM e evidência de execução | Reutilizar: estrutura no CBM, significado em Markdown, resultados em artefatos de execução. Não duplicar índice de símbolos. |


## 5. Plano e critérios de aceitação

Primeiro, reparar suíte/CI e conflitos de instruções. Depois, pilotar leitura por obrigação e sincronização condicional em project-memory, T e F, preservando schemas e fallbacks. Só então automatizar afetados e publicação segura. Atualizar o manifesto de hashes da distribuição após revisão. Rollback: rebuild completo; troca de dono exige reconciliar referências antes de remover origem.

O ensaio editorial isolado produziu resultados iguais: com 500 documentos, leituras caíram de 502 para 4 e mediana de 558,80 para 124,24 ms. Permaneceram 500 verificações de arquivos. Não mediu tokens, agentes ou produção; não prova custo proporcional ao escopo.

Comparar casos pareados de nova feature, bug entre camadas, contrato compartilhado, seleção de testes, renome/exclusão e memória stale/conflitante. Fixar respostas e evidências por inspeção de código/requisitos/execuções antes de gerar a memória. Medir correção, omissões materiais, suporte, uso stale, arquivos, tokens reais, tempo e manutenção; crescer documentos, rotas e pacotes sem mudar a tarefa.

Aceitar somente sem omissões materiais ou fatos sem suporte nos casos controlados, com IDs válidos, incerteza preservada, equivalência dos índices e publicação recuperável. Ganho operacional precisa sobreviver a repetições e crescimento; nenhum percentual arbitrário foi definido. O [anexo](EVIDENCIAS_E_AVALIACAO.md) especifica oráculos, variação e evidência exigida por etapa SDLC. Eficácia em produção permanece não demonstrada.
