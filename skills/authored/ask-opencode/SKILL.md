---
name: ask-opencode
description: Delegate tasks, consultations, or second-opinion reviews to the local OpenCode AI CLI transparently on behalf of the user. Automatically launches the headless daemon under the hood, manages sessions, selects models and reasoning efforts, extracts clean responses, and guarantees complete process termination after execution.
---

# Ask OpenCode (`ask-opencode`)

Esta skill permite ao Antigravity delegar consultas, tarefas e análises para o **OpenCode AI CLI** instalado localmente no ambiente Windows.

A premissa fundamental desta skill é a **transparência total para o usuário com ciclo de vida rigorosamente controlado**:
* O usuário faz solicitações em linguagem natural (ex: *"Pergunte ao opencode usando gpt-6-luna/xhigh..."*, *"Peça pro opencode usando deepseek-v4-pro..."*, *"O que o opencode acha dessa função?"*).
* O Antigravity gerencia a comunicação via API headless local de alta performance, eliminando travamentos de terminal comuns no Windows.
* **Garantia de Ciclo de Vida:** O processo do OpenCode é iniciado sob demanda e **obrigatoriamente morto ao final de cada uso** (ou lote de consultas), garantindo que nenhum daemon continue rodando indefinidamente em segundo plano.

---

## 1. Catálogo Completo de Modelos e Esforços (Reasoning Efforts)

O OpenCode no seu ambiente está conectado aos provedores **`opencode-go`** e **`opencode`** (free). Abaixo está o catálogo completo de todos os modelos disponíveis e suas respectivas variantes de raciocínio suportadas:

### Modelos do Provedor `opencode-go`

| Modelo (`modelID`) | Nome Amigável | Esforços de Raciocínio Suportados (`variant`) |
| :--- | :--- | :--- |
| **`gpt-6-luna`** | GPT-6 Luna | `none`, `low`, `medium`, `high`, `xhigh`, `max` |
| **`gpt-5.6-luna`** | GPT-5.6 Luna | `none`, `low`, `medium`, `high`, `xhigh`, `max` |
| **`glm-5.3`** | GLM-5.3 | `low`, `high`, `max` |
| **`glm-5.3-flash`** | GLM-5.3-Flash | `low`, `high`, `max` |
| **`glm-5.2`** | GLM-5.2 | `high`, `max` |
| **`claude-haiku-5-5`** | Claude Haiku 5.5 | `low`, `medium`, `high`, `xhigh`, `max` |
| **`deepseek-v4-pro`** | DeepSeek V4 Pro (New) | `high`, `max` |
| **`deepseek-v4.1-flash`** | DeepSeek V4.1 Flash | `low`, `high`, `max` |
| **`deepseek-v4-flash`** | DeepSeek V4 Flash | `low`, `high`, `max` |
| **`deepseek-v4-flash-vision-exp`** | DeepSeek V4 Flash Vision | `low`, `high`, `max` |
| **`grok-4.7`** | Grok 4.7 | `low`, `medium`, `high`, `xhigh` |
| **`grok-4.6`** | Grok 4.6 | `low`, `medium`, `high`, `xhigh` |
| **`qwen3.8-max`** | Qwen3.8 Max | `low`, `medium`, `xhigh` |
| **`qwen3.8-flash`** | Qwen3.8 Flash | `low`, `medium`, `xhigh` |
| **`qwen3.7-plus`** | Qwen3.7 Plus | `high`, `max` |
| **`kimi-k3`** | Kimi K3 | `max` |
| **`kimi-k2.7-code`** | Kimi K2.7 Code | Padrão |
| **`minimax-m3`** | MiniMax-M3 | `none`, `thinking` |
| **`minimax-m2.7`** | MiniMax-M2.7 | Padrão |
| **`mimo-v2.6-pro`** | MiMo-V2.6-Pro | Padrão |
| **`mimo-v2.6-flash`** | MiMo-V2.6-Flash | Padrão |
| **`mimo-v2.5-pro`** | MiMo V2.5 Pro | Padrão |
| **`mimo-v2.5`** | MiMo V2.5 | Padrão |
| **`hy4-preview`** | Hy4 preview | `none`, `high` |
| **`hy3`** | Hy3 | `none`, `low`, `high` |
| **`longcat-2.0`** | LongCat-2.0 | `low`, `medium`, `high` |
| **`longcat-2.5-preview-free`**| LongCat 2.5 Preview | `low`, `medium`, `high` |
| **`muse-spark-1.3-contributor`** | Muse Spark 1.3 | `minimal`, `low`, `medium`, `high`, `xhigh` |
| **`muse-spark-1.2-contributor`** | Muse Spark 1.2 | `minimal`, `low`, `medium`, `high`, `xhigh` |
| **`space-bunny`** | Space Bunny | `low`, `medium`, `high`, `xhigh`, `max` |

### Modelos Gratuitos (`opencode`)

| Modelo (`modelID`) | Nome Amigável | Esforços de Raciocínio Suportados (`variant`) |
| :--- | :--- | :--- |
| **`big-pickle`** | Big Pickle | Padrão |
| **`exo-free`** | Exo Free | `high` |
| **`fledge-alpha-free`** | Fledge Alpha Free | `low`, `high`, `max` |
| **`ling-3.1-flash-free`** | Ling 3.1 Flash Free | `low`, `medium`, `high` |
| **`ling-3.0-flash-fin-free`** | Ling 3.0 Flash Fin Free | `low`, `medium`, `high` |
| **`longcat-2.5-preview-free`** | LongCat 2.5 Preview Free | `low`, `medium`, `high` |
| **`mimo-v2.6-flash-free`** | MiMo-V2.6-Flash Free | Padrão |
| **`muse-spark-1.3-contributor-free`** | Muse Spark 1.3 Free | `minimal`, `low`, `medium`, `high`, `xhigh` |
| **`nemotron-3.5-lightning-free`** | Nemotron 3.5 Lightning | Padrão |
| **`nemotron-3-ultra-free`** | Nemotron 3 Ultra Free | Padrão |
| **`space-bunny-free`** | Space Bunny Free | `low`, `medium`, `high`, `xhigh`, `max` |

---

## 2. Tabela de Equivalência de Reasoning Effort (PT / EN)

A skill normaliza automaticamente termos em inglês e português:

| Variant Nativo | Aliases Aceitos na Invocação |
| :--- | :--- |
| `none` | `none`, `nenhum`, `zero`, `off` |
| `minimal` | `minimal`, `minimo`, `mínimo`, `min` |
| `low` | `low`, `baixo` |
| `medium` | `medium`, `medio`, `médio`, `med` |
| `high` | `high`, `alto` |
| `xhigh` | `xhigh`, `extra-high`, `extra_high`, `extra-alto`, `extra_alto`, `extra` |
| `max` | `max`, `maximo`, `máximo`, `maximum` |
| `thinking` | `thinking` |

---

## 3. Mecânica de Invocação e Controle de Processos

A skill utiliza o script auxiliar [Invoke-Opencode.ps1](file:///__HOME__/.gemini/config/skills/ask-opencode/scripts/Invoke-Opencode.ps1).

### Exemplo de Chamada com AutoKill (Comportamento Padrão)
```powershell
powershell -ExecutionPolicy Bypass -File "__HOME__\.gemini\config\skills\ask-opencode\scripts\Invoke-Opencode.ps1" `
  -Prompt "Explique a diferença entre mutex e semáforo" `
  -Model "gpt-6-luna/xhigh"
```

### Exemplo com Modelo Gratuito
```powershell
powershell -ExecutionPolicy Bypass -File "__HOME__\.gemini\config\skills\ask-opencode\scripts\Invoke-Opencode.ps1" `
  -Prompt "Valide esta expressão regular" `
  -Model "big-pickle"
```

### Forçar Limpeza Manual de Processos Residuais
Caso necessário, o agente ou você podem forçar a morte imediata de qualquer processo residual do OpenCode a qualquer momento:
```powershell
powershell -ExecutionPolicy Bypass -File "__HOME__\.gemini\config\skills\ask-opencode\scripts\Invoke-Opencode.ps1" -KillOnly
```
