---
name: ask-codex
description: Delegate tasks, consultations, code reviews, or isolated implementations to the local OpenAI Codex CLI (codex-cli) transparently on behalf of the user. Automatically determines the optimal execution profile (read-only, review, worktree isolation, or structured extraction) and handles all Windows/PowerShell CLI nuances.
---

# Ask Codex (`ask-codex`)

Esta skill permite ao Antigravity orquestrar e delegar tarefas ao **OpenAI Codex CLI (`codex-cli`)** instalado localmente no ambiente Windows.

A premissa fundamental desta skill é a **transparência total para o usuário**:
* O usuário não precisa conhecer comandos de terminal, flags (`--sandbox`, `--worktree`, `--approve-for-me`, `-c model=...`), pipes de PowerShell ou arquivos temporários.
* O usuário faz solicitações em linguagem natural (ex: *"Pergunte ao codex o que ele acha dessa função"*, *"Peça pro codex revisar minhas alterações usando gpt-6-luna/extra-high"*, *"Manda o codex refatorar essa rotina de forma isolada"*).
* O Antigravity interpreta a intenção, identifica o modelo e esforço de raciocínio desejados, seleciona o perfil técnico de execução adequado, gerencia a chamada em background e entrega uma resposta clara, consolidada e acionável.

---

## 1. Matriz de Interpretação e Roteamento de Intenção

Quando o usuário pedir interação com o Codex, analise a intenção e selecione o perfil técnico correspondente:

| Intenção do Usuário | Exemplo de Pedido | Perfil Técnico | Mecânica CLI |
| :--- | :--- | :--- | :--- |
| **Consulta / Opinião / Análise** | *"Pergunte ao codex se essa lógica tem falhas"*, *"O que o codex acha de..."* | **ReadOnly** | `--sandbox read-only --ephemeral` |
| **Revisão de Código** | *"Peça pro codex revisar meu diff"*, *"Manda o codex auditar os arquivos não comitados"* | **Review** | `codex review --uncommitted` |
| **Implementação / Refatoração Experimental** | *"Peça pro codex implementar a função X isoladamente"*, *"Manda o codex refatorar isso"* | **WorktreeWrite** (Isolado) | `--worktree --sandbox workspace-write --approve-for-me` |
| **Alteração Direta (Autorizada)** | *"Peça pro codex aplicar a correção diretamente no código"* | **WorkspaceWrite** | `--sandbox workspace-write --approve-for-me` |
| **Diagnóstico Estruturado** | *"Peça pro codex um relatório JSON de vulnerabilidades"* | **Structured JSON** | `--output-schema <schema.json> -o <out.json>` |

---

## 2. Seleção de Modelos e Esforço de Raciocínio (Reasoning Effort)

O usuário pode opcionalmente especificar qual modelo ou perfil de raciocínio o Codex deve utilizar para a tarefa.

### Valores Padrão do Ambiente
* **Modelo Padrão:** Definido no arquivo `~/.codex/config.toml` (atualmente `gpt-6.1-sol`).
* **Esforço de Raciocínio Padrão:** `low`.

### Modelos Disponíveis
* `gpt-6.1-sol` (padrão)
* `gpt-6-luna`
* `gpt-5.6-sol`
* Outros modelos suportados pela conta OpenAI do usuário (ex: `o3`).

### Níveis de Esforço de Raciocínio (`reasoning.effort`)
O Codex e a API da OpenAI suportam 7 níveis nativos. A skill mapeia e normaliza aliases em inglês e português automaticamente:

| Nível Nativo (OpenAI/Codex) | Descrição | Aliases Aceitos na Invocação |
| :--- | :--- | :--- |
| `none` | Desativa o raciocínio estendido | `none`, `nenhum`, `zero`, `off` |
| `minimal` | Raciocínio mínimo para resposta rápida | `minimal`, `minimo`, `mínimo`, `min` |
| `low` *(Padrão atual)* | Raciocínio leve (configurado no seu `config.toml`) | `low`, `baixo` |
| `medium` | Raciocínio equilibrado | `medium`, `medio`, `médio`, `med` |
| `high` | Raciocínio aprofundado para problemas complexos | `high`, `alto` |
| `xhigh` | Raciocínio extra-alto para tarefas de alta precisão | `xhigh`, `extra-high`, `extra_high`, `extra-alto`, `extra_alto`, `extra` |
| `max` | Limite máximo de esforço permitido pelo modelo | `max`, `maximo`, `máximo`, `maximum` |

### Notação Combinada em Linguagem Natural
O usuário pode solicitar diretamente no formato `modelo/esforço`:
* *"Peça pro codex usando `gpt-6-luna/extra-high`..."*
* *"Consulte o codex com `o3/high`..."*

---

## 3. Nuances Técnicas no Windows / PowerShell

> [!IMPORTANT]
> **Regra de Ouro do Stdin:** No PowerShell, o `codex exec` entra em bloqueio de terminal (aguardando EOF) se invocado sem pipe ou redirecionamento de entrada. **Nunca** invoque `codex exec` sem fechar o stdin.

### Como Invocar

Sempre utilize uma das duas abordagens abaixo:

### Opção A: Helper Script Embutido (Recomendado)
A skill inclui o script auxiliar [Invoke-Codex.ps1](file:///__HOME__/.gemini/config/skills/ask-codex/scripts/Invoke-Codex.ps1):

```powershell
# Consulta Read-Only com modelo padrão
powershell -ExecutionPolicy Bypass -File "__HOME__\.gemini\config\skills\ask-codex\scripts\Invoke-Codex.ps1" `
  -Prompt "Analise se a função calculateTax possui edge cases não tratados" `
  -Mode ReadOnly

# Consulta com modelo específico e esforço de raciocínio (notação combinada)
powershell -ExecutionPolicy Bypass -File "__HOME__\.gemini\config\skills\ask-codex\scripts\Invoke-Codex.ps1" `
  -Prompt "Analise a complexidade ciclomática desta rotina" `
  -Model "gpt-6-luna/extra-high" `
  -Mode ReadOnly

# Revisão de código não comitado
powershell -ExecutionPolicy Bypass -File "__HOME__\.gemini\config\skills\ask-codex\scripts\Invoke-Codex.ps1" `
  -Mode Review `
  -ReviewTarget "--uncommitted"

# Implementação em Git Worktree descartável (não afeta o branch ativo)
powershell -ExecutionPolicy Bypass -File "__HOME__\.gemini\config\skills\ask-codex\scripts\Invoke-Codex.ps1" `
  -Prompt "Adicione validação de entrada e crie testes unitários para o módulo Auth" `
  -Model "gpt-6-luna" `
  -ReasoningEffort "xhigh" `
  -Mode WorktreeWrite
```

### Opção B: Invocação Direta via One-Liner
Quando invocar diretamente via comando PowerShell:

```powershell
$tmp = [System.IO.Path]::GetTempFileName(); `
"Sua pergunta aqui" | codex exec --skip-git-repo-check --sandbox read-only --ephemeral -c model="gpt-6-luna" -c model_reasoning_effort="xhigh" -o $tmp - 2>$null; `
Get-Content $tmp -Raw -Encoding UTF8; `
Remove-Item $tmp -Force
```

---

## 4. Protocolo de Postura e Apresentação de Resultados

Ao devolver a resposta para o usuário:

1. **Síntese Inteligente:** Não exponha logs brutos do terminal, traces do codex ou metadados de subprocesso a menos que relevante. Apresente a análise ou parecer do Codex com clareza (mencionando o modelo utilizado se tiver sido personalizado).
2. **Sparring Partner / Validação Cruzada:** Como o Codex (GPT) e você (Gemini) são modelos distintos, agregue valor comentando se concorda ou se identificou algum ponto adicional que o Codex não observou.
3. **Gerenciamento de Worktree (Se aplicável):**
   * Se o Codex gerou código em um worktree (`WorktreeWrite`), informe ao usuário o que foi produzido.
   * Inspecione o diff do worktree gerado antes de sugerir a integração com o branch de trabalho.
   * Pergunte ao usuário se ele deseja aprovar a mesclagem ou descartar o experimento.
