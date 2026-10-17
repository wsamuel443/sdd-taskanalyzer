# Especificação SDD — TaskAnalyzer (v1.0.0)

Autor: Wagner Samuel Cardoso Alves da Silva — Bootcamp III (Fase 1, transposta para Markdown).

## 1. Propósito

O TaskAnalyzer recebe um conjunto de tarefas e calcula métricas objetivas de
desempenho a partir de datas e status. Não gerencia o ciclo de vida das tarefas:
é estritamente analítico.

## 2. Contrato de interface

### 2.1 Entradas (cada tarefa)

| Campo | Tipo | Obrigatório | Restrições |
|---|---|---|---|
| `id_tarefa` | int | Sim | > 0 |
| `titulo` | str | Sim | não vazio |
| `prioridade` | str | Sim | `"baixa"`, `"media"`, `"alta"` |
| `status` | str | Sim | `"pendente"`, `"em_andamento"`, `"concluida"`, `"cancelada"` |
| `data_criacao` | datetime (UTC) | Sim | |
| `data_inicio` | datetime (UTC) | Não | |
| `prazo` | datetime (UTC) | Sim | |
| `data_conclusao` | datetime (UTC) | Não | obrigatória se `status == "concluida"` |

### 2.2 Saídas

| Campo | Tipo | Descrição |
|---|---|---|
| `tempo_medio_conclusao_horas` | float | média (h) entre início e conclusão das tarefas concluídas |
| `taxa_atraso_percentual` | float | % de tarefas em atraso |
| `quantidade_tarefas` | int | total de tarefas válidas recebidas |
| `indicadores_por_prioridade` | dict | por `baixa`/`media`/`alta`: `quantidade`, `tempo_medio_conclusao_horas`, `taxa_atraso_percentual` |
| `total_tarefas`, `total_concluidas`, `total_pendentes` | int | contadores exigidos pelo desafio da Fase 2 (`total_tarefas == quantidade_tarefas`; pendentes = `pendente` + `em_andamento`) |

### 2.3 Regras de negócio

- Só tarefas `concluida` entram no tempo médio.
- `cancelada` conta em `quantidade_tarefas`, mas fica fora dos cálculos de tempo e atraso.
- Em atraso: (a) concluída com `data_conclusao > prazo`; ou (b) não concluída com `prazo` anterior ao momento da análise.
- `data_conclusao` anterior a `data_inicio` (ou a `data_criacao`) é entrada inválida → `TaskValidationError`.
- Todo cálculo de datas em UTC.
- Divisão por zero tratada explicitamente: retorna `0.0`, nunca exceção não tratada.

## 3. Cenários de aceite (Dado–Quando–Então)

**Cenário 1 — Sucesso.** Dado um conjunto de tarefas válidas, quando o analisador for
executado, então retorna `tempo_medio_conclusao_horas`, `taxa_atraso_percentual`,
`quantidade_tarefas` e `indicadores_por_prioridade` corretos.

**Cenário 2 — Erro.** Dado uma entrada com datas inválidas (ex.: `data_conclusao`
anterior a `data_inicio`), quando o analisador for executado, então dispara
`TaskValidationError` com mensagem clara.

**Casos de borda:** lista vazia; apenas tarefas pendentes; prazo igual à conclusão
(não é atraso); prioridade fora do enum.

## 4. Decisões de reconciliação (spec Fase 1 × desafio Fase 2)

1. **Nome da exceção:** a Fase 1 cita `TarefaInvalidaError`/`DadosInsuficientesError`
   como exemplos; o desafio da Fase 2 exige `TaskValidationError`. Adotado `TaskValidationError`.
2. **Lista vazia:** a Fase 1 sugeria exceção; o desafio da Fase 2 exige retorno `0.0`
   sem exceção. Prevalece o desafio (retorno de zeros).
3. **Chaves de saída:** mantidas as do contrato da Fase 1, acrescidas de
   `total_tarefas`, `total_concluidas` e `total_pendentes` (exigidas pelo desafio).
4. **Tarefa concluída sem `data_inicio`:** usa-se `data_criacao` como referência do tempo.
5. **Assinatura pública:** `analyze_tasks(tarefas, agora=None)`; `agora` (UTC) permite
   testes determinísticos do critério de prazo vencido.

## 5. Estrutura do repositório

```
sdd-taskanalyzer/
├── README.md
├── CONTEXT_RULES.md
├── .gitignore
├── requirements.txt
├── specs/task_analyzer_spec.md
├── tests/test_harness.py
└── src/task_analyzer.py
```
