# sdd-taskanalyzer

![Tests](https://img.shields.io/badge/tests-pytest-brightgreen) ![Python](https://img.shields.io/badge/python-3.11%2B-blue)

Módulo **TaskAnalyzer** desenvolvido com **Spec-Driven Development (SDD)** e assistência de IA
(Bootcamp III — Fase 2). O código em `src/task_analyzer.py` foi gerado por IA guiada por
[`CONTEXT_RULES.md`](CONTEXT_RULES.md) e [`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md),
e homologado por revisão humana.

## Estrutura

```
├── CONTEXT_RULES.md          # regras de governança para a IA
├── specs/task_analyzer_spec.md
├── src/task_analyzer.py      # analyze_tasks + TaskValidationError
├── tests/test_harness.py     # suíte pytest (cenários 1, 2 e bordas)
├── requirements.txt
└── .gitignore
```

## Como executar

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest -v
```

## Exemplo de uso

```python
from datetime import datetime, timezone
from src.task_analyzer import analyze_tasks

utc = timezone.utc
tarefas = [{
    "id_tarefa": 1, "titulo": "Entregar relatório", "prioridade": "alta",
    "status": "concluida",
    "data_criacao": datetime(2026, 1, 1, 8, tzinfo=utc),
    "data_inicio": datetime(2026, 1, 2, 8, tzinfo=utc),
    "prazo": datetime(2026, 1, 3, 8, tzinfo=utc),
    "data_conclusao": datetime(2026, 1, 2, 18, tzinfo=utc),
}]
print(analyze_tasks(tarefas))
```

## Fluxo de Git

`main` + branches `feature/sdd-specification`, `feature/task-analyzer-impl`,
`feature/test-harness`, integradas via Pull Request com revisão humana.

## Status do build

Fase 2 (implementação, test harness e versionamento). A Fase 3 adicionará CI/CD (GitHub Actions) e Docker.
