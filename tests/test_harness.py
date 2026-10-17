"""Test Harness do TaskAnalyzer (pytest).

Traduz os cenários de aceite da Fase 1:
    Cenário 1 - Sucesso; Cenário 2 - Exceção/Erro; e casos de borda.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from task_analyzer import TaskValidationError, analyze_tasks  # noqa: E402

UTC = timezone.utc
AGORA = datetime(2026, 1, 10, 12, 0, tzinfo=UTC)


def _tarefa(id_tarefa: int, **extra: Any) -> dict[str, Any]:
    """Cria uma tarefa válida, permitindo sobrescrever campos."""
    base: dict[str, Any] = {
        "id_tarefa": id_tarefa,
        "titulo": f"Tarefa {id_tarefa}",
        "prioridade": "media",
        "status": "pendente",
        "data_criacao": datetime(2026, 1, 1, 8, 0, tzinfo=UTC),
        "prazo": datetime(2026, 1, 20, 8, 0, tzinfo=UTC),
    }
    base.update(extra)
    return base


@pytest.fixture
def tarefas_validas() -> list[dict[str, Any]]:
    """Conjunto misto com resultados calculados à mão.

    - 1 alta, concluída em 10h, no prazo.
    - 2 alta, concluída em 20h, com atraso.
    - 3 media, concluída em 6h, no prazo.
    - 4 baixa, pendente com prazo vencido (atraso).
    - 5 baixa, em andamento dentro do prazo.
    - 6 media, cancelada (conta só na quantidade).
    """
    ini = datetime(2026, 1, 2, 8, 0, tzinfo=UTC)
    return [
        _tarefa(1, prioridade="alta", status="concluida", data_inicio=ini,
                data_conclusao=ini + timedelta(hours=10),
                prazo=ini + timedelta(hours=12)),
        _tarefa(2, prioridade="alta", status="concluida", data_inicio=ini,
                data_conclusao=ini + timedelta(hours=20),
                prazo=ini + timedelta(hours=15)),
        _tarefa(3, prioridade="media", status="concluida", data_inicio=ini,
                data_conclusao=ini + timedelta(hours=6),
                prazo=ini + timedelta(hours=6)),
        _tarefa(4, prioridade="baixa", status="pendente",
                prazo=datetime(2026, 1, 5, 8, 0, tzinfo=UTC)),
        _tarefa(5, prioridade="baixa", status="em_andamento",
                data_inicio=ini),
        _tarefa(6, prioridade="media", status="cancelada"),
    ]


# ---------------- Cenário 1: sucesso ----------------

def test_sucesso_calculo_metricas(tarefas_validas: list[dict[str, Any]]) -> None:
    r = analyze_tasks(tarefas_validas, agora=AGORA)
    assert r["total_tarefas"] == 6
    assert r["quantidade_tarefas"] == 6
    assert r["total_concluidas"] == 3
    assert r["total_pendentes"] == 2
    # (10 + 20 + 6) / 3 = 12.0
    assert r["tempo_medio_conclusao_horas"] == 12.0
    # ativas = 5; atrasadas = tarefa 2 e tarefa 4 -> 2/5 = 40%
    assert r["taxa_atraso_percentual"] == 40.0


def test_sucesso_indicadores_por_prioridade(
    tarefas_validas: list[dict[str, Any]],
) -> None:
    ind = analyze_tasks(tarefas_validas, agora=AGORA)["indicadores_por_prioridade"]
    assert set(ind) == {"baixa", "media", "alta"}
    assert ind["alta"] == {
        "quantidade": 2,
        "tempo_medio_conclusao_horas": 15.0,
        "taxa_atraso_percentual": 50.0,
    }
    # media: tarefa 3 (concluída no limite do prazo) + tarefa 6 cancelada
    assert ind["media"] == {
        "quantidade": 2,
        "tempo_medio_conclusao_horas": 6.0,
        "taxa_atraso_percentual": 0.0,
    }
    # baixa: sem concluídas; 1 de 2 atrasada
    assert ind["baixa"] == {
        "quantidade": 2,
        "tempo_medio_conclusao_horas": 0.0,
        "taxa_atraso_percentual": 50.0,
    }


def test_prazo_igual_a_conclusao_nao_e_atraso() -> None:
    ini = datetime(2026, 1, 2, tzinfo=UTC)
    t = _tarefa(1, status="concluida", data_inicio=ini,
                data_conclusao=ini + timedelta(hours=4),
                prazo=ini + timedelta(hours=4))
    assert analyze_tasks([t], agora=AGORA)["taxa_atraso_percentual"] == 0.0


def test_canceladas_ficam_fora_dos_calculos() -> None:
    tarefas = [_tarefa(1, status="cancelada",
                       prazo=datetime(2026, 1, 2, tzinfo=UTC))]
    r = analyze_tasks(tarefas, agora=AGORA)
    assert r["quantidade_tarefas"] == 1
    assert r["taxa_atraso_percentual"] == 0.0
    assert r["tempo_medio_conclusao_horas"] == 0.0


def test_sem_data_inicio_usa_data_criacao() -> None:
    criacao = datetime(2026, 1, 1, 8, 0, tzinfo=UTC)
    t = _tarefa(1, status="concluida", data_criacao=criacao,
                data_conclusao=criacao + timedelta(hours=5))
    assert analyze_tasks([t], agora=AGORA)["tempo_medio_conclusao_horas"] == 5.0


# ---------------- Cenário 2: exceções ----------------

def test_erro_data_conclusao_anterior_inicio() -> None:
    ini = datetime(2026, 1, 5, tzinfo=UTC)
    t = _tarefa(1, status="concluida", data_inicio=ini,
                data_conclusao=ini - timedelta(hours=1))
    with pytest.raises(TaskValidationError, match="data_inicio"):
        analyze_tasks([t], agora=AGORA)


def test_erro_data_conclusao_anterior_criacao() -> None:
    criacao = datetime(2026, 1, 5, tzinfo=UTC)
    t = _tarefa(1, status="concluida", data_criacao=criacao,
                data_conclusao=criacao - timedelta(days=1))
    with pytest.raises(TaskValidationError, match="data_criacao"):
        analyze_tasks([t], agora=AGORA)


def test_erro_concluida_sem_data_conclusao() -> None:
    with pytest.raises(TaskValidationError, match="data_conclusao"):
        analyze_tasks([_tarefa(1, status="concluida")], agora=AGORA)


def test_erro_prioridade_fora_do_enum() -> None:
    with pytest.raises(TaskValidationError, match="prioridade"):
        analyze_tasks([_tarefa(1, prioridade="urgente")], agora=AGORA)


def test_erro_status_invalido() -> None:
    with pytest.raises(TaskValidationError, match="status"):
        analyze_tasks([_tarefa(1, status="arquivada")], agora=AGORA)


def test_erro_campo_obrigatorio_ausente() -> None:
    t = _tarefa(1)
    del t["prazo"]
    with pytest.raises(TaskValidationError, match="prazo"):
        analyze_tasks([t], agora=AGORA)


def test_erro_titulo_vazio_e_id_invalido() -> None:
    with pytest.raises(TaskValidationError, match="titulo"):
        analyze_tasks([_tarefa(1, titulo="  ")], agora=AGORA)
    with pytest.raises(TaskValidationError, match="id_tarefa"):
        analyze_tasks([_tarefa(0)], agora=AGORA)


def test_erro_data_sem_fuso_ou_fora_de_utc() -> None:
    ingenua = datetime(2026, 1, 1, 8, 0)
    with pytest.raises(TaskValidationError, match="UTC"):
        analyze_tasks([_tarefa(1, data_criacao=ingenua)], agora=AGORA)
    br = timezone(timedelta(hours=-3))
    with pytest.raises(TaskValidationError, match="UTC"):
        analyze_tasks([_tarefa(1, prazo=datetime(2026, 1, 2, tzinfo=br))],
                      agora=AGORA)


def test_erro_tipo_de_data_invalido() -> None:
    with pytest.raises(TaskValidationError, match="datetime"):
        analyze_tasks([_tarefa(1, prazo="2026-01-20")], agora=AGORA)


def test_erro_agora_fora_de_utc() -> None:
    with pytest.raises(TaskValidationError, match="agora"):
        analyze_tasks([], agora=datetime(2026, 1, 1))


def test_erro_em_uma_tarefa_invalida_o_lote() -> None:
    tarefas = [_tarefa(1), _tarefa(2, prioridade="x")]
    with pytest.raises(TaskValidationError):
        analyze_tasks(tarefas, agora=AGORA)


# ---------------- Casos de borda ----------------

def test_borda_lista_vazia_retorna_zeros() -> None:
    r = analyze_tasks([], agora=AGORA)
    assert r["total_tarefas"] == 0
    assert r["total_concluidas"] == 0
    assert r["total_pendentes"] == 0
    assert r["tempo_medio_conclusao_horas"] == 0.0
    assert r["taxa_atraso_percentual"] == 0.0
    for grupo in r["indicadores_por_prioridade"].values():
        assert grupo == {
            "quantidade": 0,
            "tempo_medio_conclusao_horas": 0.0,
            "taxa_atraso_percentual": 0.0,
        }


def test_borda_apenas_pendentes_sem_excecao() -> None:
    tarefas = [
        _tarefa(1, status="pendente"),
        _tarefa(2, status="em_andamento", prioridade="alta"),
    ]
    r = analyze_tasks(tarefas, agora=AGORA)
    assert r["total_concluidas"] == 0
    assert r["total_pendentes"] == 2
    assert r["tempo_medio_conclusao_horas"] == 0.0
    assert r["taxa_atraso_percentual"] == 0.0


def test_borda_apenas_pendentes_com_prazo_vencido() -> None:
    t = _tarefa(1, prazo=datetime(2026, 1, 2, tzinfo=UTC))
    r = analyze_tasks([t], agora=AGORA)
    assert r["taxa_atraso_percentual"] == 100.0
    assert r["tempo_medio_conclusao_horas"] == 0.0


def test_borda_tarefas_em_atraso_pelo_prazo_exato_nao_vencido() -> None:
    t = _tarefa(1, prazo=AGORA)  # prazo == agora: ainda não vencido
    assert analyze_tasks([t], agora=AGORA)["taxa_atraso_percentual"] == 0.0


def test_agora_padrao_usa_utc_atual() -> None:
    t = _tarefa(1, prazo=datetime(2000, 1, 1, tzinfo=UTC))
    assert analyze_tasks([t])["taxa_atraso_percentual"] == 100.0
