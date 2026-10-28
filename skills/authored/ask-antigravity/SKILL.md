---
name: ask-antigravity
description: Delegate consultations, code reviews, implementations, or structured reports to the locally installed Google Antigravity CLI (agy) on behalf of the user. Use when the user asks to consult or assign work to Antigravity.
---

# Ask Antigravity

Permite ao Codex ou outro agente delegar tarefas ao **Antigravity CLI (`agy`)** no Windows/PowerShell. Interprete o pedido em linguagem natural, prepare o contexto e apresente uma resposta consolidada; o usuário não precisa conhecer flags ou arquivos temporários.

## Preparação

- Confirme `Get-Command agy` e consulte `agy --help` antes de assumir suporte a flags. Não confunda o CLI `agy` com o launcher do editor `antigravity`.
- Use a autenticação existente. Se faltar login, informe o bloqueio e oriente a autenticação interativa com `agy`; não copie credenciais nem instale ferramentas automaticamente.
- Execute no diretório do projeto solicitado. Cada chamada recebe contexto próprio: inclua objetivo, arquivos relevantes, critérios de aceitação e limites da autorização. Não envie segredos.
- Use [scripts/Invoke-Antigravity.ps1](scripts/Invoke-Antigravity.ps1), resolvendo o caminho a partir da pasta desta skill.

## Roteamento

| Pedido | Execução |
| --- | --- |
| Consulta, opinião ou análise | `-Mode ReadOnly`: `--mode plan --sandbox` e instrução de não alterar arquivos. |
| Revisão de código | `-Mode Review`: mesmo modo de planejamento; inclua alvo, base ou diff no prompt. Não existe pressuposto de um subcomando `review`. |
| Implementação isolada | Crie um Git worktree e execute `-Mode WorkspaceWrite -WorkingDirectory <worktree>`. |
| Alteração direta autorizada | `-Mode WorkspaceWrite -WorkingDirectory <projeto>`: `--mode accept-edits --sandbox`. |
| Relatório estruturado | Combine o modo apropriado com `-OutputSchema <schema.json>`; o helper retorna `structured_output` serializado. |

`ReadOnly` expressa intenção de planejamento; não equivale ao sandbox `read-only` do Codex. `--sandbox` restringe comandos, mas não deve ser apresentado como garantia de isolamento absoluto. Preserve as permissões locais: não use `--dangerously-skip-permissions`, YOLO ou alterações globais para contornar bloqueios. Ferramentas podem ser negadas em headless mesmo quando o processo termina com sucesso; confira avisos em stderr e a completude da resposta.

## Modelos e esforço

Descubra modelos com `agy models`. Sem escolha explícita, mantenha os padrões do CLI; não fixe catálogo ou modelo nesta skill.

O helper aceita `-Model <slug>`, `-ReasoningEffort low|medium|high|xhigh|max` e a notação `-Model <slug>/extra-high`. Normalize `baixo`, `médio`, `alto`, `extra-high`, `extra-alto` e `máximo`. Um esforço separado prevalece sobre o sufixo. A disponibilidade depende do modelo e da versão instalada; não substitua silenciosamente uma escolha rejeitada.

## Exemplos

Nos exemplos, `$skillRoot` representa o caminho absoluto da pasta desta skill.

```powershell
& "$skillRoot\scripts\Invoke-Antigravity.ps1" `
  -Prompt 'Analise os casos de borda de calculateTax em src/tax.py.' `
  -Mode ReadOnly -WorkingDirectory 'C:\projetos\app'

& "$skillRoot\scripts\Invoke-Antigravity.ps1" `
  -Prompt 'Revise o diff não comitado. Informe bugs com arquivo, linha e impacto; não edite arquivos.' `
  -Mode Review -WorkingDirectory 'C:\projetos\app' -ReasoningEffort high

& "$skillRoot\scripts\Invoke-Antigravity.ps1" `
  -Prompt 'Liste os riscos do módulo Auth conforme o schema fornecido.' `
  -OutputSchema 'C:\projetos\risk.schema.json' -WorkingDirectory 'C:\projetos\app'
```

O helper fecha stdin, mantém stderr visível, valida código de saída e status JSON, e define um limite de dez minutos. Use `-TimeoutSeconds` para ajustar. `-OutputFile` salva somente uma resposta bem-sucedida em UTF-8. Não continue conversas anteriores automaticamente.

## Implementação isolada

Escolha um caminho novo fora da árvore atual e um nome de branch livre. Crie o worktree com `git worktree add -b <branch> <caminho> HEAD`, verificando o código de saída. Ele parte de `HEAD`: alterações não commitadas não são transferidas. Se forem necessárias, prepare explicitamente o contexto sem sobrescrever trabalho existente.

Execute o helper com `-Mode WorkspaceWrite` nesse worktree e informe o caminho ao usuário. Inspecione diff e testes antes de integrar. Preserve o worktree se houver falha ou trabalho a revisar. Integre somente dentro da autorização recebida; não remova branches ou worktrees automaticamente. Worktree isola arquivos versionados, não serviços externos nem credenciais.

## Entrega

Resuma o parecer do Antigravity e identifique modelo/esforço quando solicitados. Separe as conclusões dele da sua avaliação. Para mudanças, informe arquivos, validações executadas e limitações. Não declare testes executados quando ferramentas foram negadas. Em falha, reporte o erro e preserve o trabalho; não repita automaticamente ações com possíveis efeitos externos.

Referências oficiais: [headless](https://antigravity.google/docs/cli/headless/) e [CLI](https://antigravity.google/docs/cli/reference/). Em divergência, confira o `--help` da instalação local.
