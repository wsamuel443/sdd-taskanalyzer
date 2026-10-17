"""Módulo TaskAnalyzer: análise de tarefas e produtividade.

Módulo puramente analítico e em memória. Recebe uma lista de tarefas e
calcula métricas objetivas (tempo médio de conclusão, taxa de atraso,
contagens e indicadores por prioridade), conforme o contrato definido em
``specs/task_analyzer_spec.md``.

Todas as datas devem ser ``datetime`` com fuso horário UTC.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

PRIORIDADES_VALIDAS: tuple[str, ...] = ("baixa", "media", "alta")
STATUS_VALIDOS: frozenset[str] = frozenset(
    {"pendente", "em_andamento", "concluida", "cancelada"}
)
_CAMPOS_OBRIGATORIOS: tuple[str, ...] = (
    "id_tarefa",
    "titulo",
    "prioridade",
    "status",
    "data_criacao",
    "prazo",
)
_CAMPOS_DATA: tuple[str, ...] = (
    "data_criacao",
    "data_inicio",
    "prazo",
    "data_conclusao",
)


class TaskValidationError(ValueError):
    """Erro de validação de uma tarefa ou do conjunto de entrada."""


def _validar_data(valor: Any, campo: str, id_tarefa: Any) -> None:
    """Garante que ``valor`` é um datetime ciente de fuso e em UTC.

    Args:
        valor: Valor do campo de data.
        campo: Nome do campo (para a mensagem de erro).
        id_tarefa: Identificador da tarefa (para a mensagem de erro).

    Raises:
        TaskValidationError: Se o valor não for datetime, for ingênuo
            (sem fuso) ou não estiver em UTC.
    """
    if not isinstance(valor, datetime):
        raise TaskValidationError(
            f"Tarefa {id_tarefa}: '{campo}' deve ser um datetime."
        )
    if valor.tzinfo is None or valor.utcoffset() != timedelta(0):
        raise TaskValidationError(
            f"Tarefa {id_tarefa}: '{campo}' deve estar em UTC."
        )


def _validar_campos_basicos(tarefa: Mapping[str, Any]) -> None:
    """Valida presença, tipos e enums dos campos de uma tarefa.

    Args:
        tarefa: Dicionário representando a tarefa.

    Raises:
        TaskValidationError: Se algum campo estiver ausente ou inválido.
    """
    for campo in _CAMPOS_OBRIGATORIOS:
        if campo not in tarefa or tarefa[campo] is None:
            raise TaskValidationError(
                f"Tarefa {tarefa.get('id_tarefa', '?')}: campo obrigatório "
                f"'{campo}' ausente."
            )

    id_tarefa = tarefa["id_tarefa"]
    if (
        not isinstance(id_tarefa, int)
        or isinstance(id_tarefa, bool)
        or id_tarefa <= 0
    ):
        raise TaskValidationError(
            f"Tarefa {id_tarefa}: 'id_tarefa' deve ser um inteiro > 0."
        )
    if not isinstance(tarefa["titulo"], str) or not tarefa["titulo"].strip():
        raise TaskValidationError(
            f"Tarefa {id_tarefa}: 'titulo' não pode ser vazio."
        )
    if tarefa["prioridade"] not in PRIORIDADES_VALIDAS:
        raise TaskValidationError(
            f"Tarefa {id_tarefa}: prioridade inválida "
            f"'{tarefa['prioridade']}'. Aceitas: {PRIORIDADES_VALIDAS}."
        )
    if tarefa["status"] not in STATUS_VALIDOS:
        raise TaskValidationError(
            f"Tarefa {id_tarefa}: status inválido '{tarefa['status']}'."
        )


def validate_task(tarefa: Mapping[str, Any]) -> None:
    """Valida uma única tarefa conforme o contrato de entrada.

    Args:
        tarefa: Dicionário com os campos da tarefa.

    Raises:
        TaskValidationError: Se a tarefa violar qualquer regra do contrato,
            incluindo datas inconsistentes (``data_conclusao`` anterior a
            ``data_criacao`` ou a ``data_inicio``).
    """
    _validar_campos_basicos(tarefa)
    id_tarefa = tarefa["id_tarefa"]

    for campo in _CAMPOS_DATA:
        if tarefa.get(campo) is not None:
            _validar_data(tarefa[campo], campo, id_tarefa)

    conclusao = tarefa.get("data_conclusao")
    if tarefa["status"] == "concluida" and conclusao is None:
        raise TaskValidationError(
            f"Tarefa {id_tarefa}: 'data_conclusao' é obrigatória quando "
            "o status é 'concluida'."
        )
    if conclusao is None:
        return

    if conclusao < tarefa["data_criacao"]:
        raise TaskValidationError(
            f"Tarefa {id_tarefa}: data_conclusao anterior a data_criacao."
        )
    inicio = tarefa.get("data_inicio")
    if inicio is not None and conclusao < inicio:
        raise TaskValidationError(
            f"Tarefa {id_tarefa}: data_conclusao anterior a data_inicio."
        )


def _horas_de_execucao(tarefa: Mapping[str, Any]) -> float:
    """Calcula as horas entre início (ou criação) e conclusão.

    Quando ``data_inicio`` não foi informada, usa ``data_criacao`` como
    referência.

    Args:
        tarefa: Tarefa concluída e já validada.

    Returns:
        Duração em horas.
    """
    inicio = tarefa.get("data_inicio") or tarefa["data_criacao"]
    return (tarefa["data_conclusao"] - inicio).total_seconds() / 3600.0


def _esta_em_atraso(tarefa: Mapping[str, Any], agora: datetime) -> bool:
    """Indica se a tarefa está (ou terminou) em atraso.

    Args:
        tarefa: Tarefa válida e não cancelada.
        agora: Instante de referência da análise (UTC).

    Returns:
        True se concluída após o prazo, ou não concluída com prazo vencido.
    """
    if tarefa["status"] == "concluida":
        return bool(tarefa["data_conclusao"] > tarefa["prazo"])
    return bool(tarefa["prazo"] < agora)


def _media(valores: Sequence[float]) -> float:
    """Média aritmética segura: retorna 0.0 para sequência vazia.

    Args:
        valores: Valores numéricos.

    Returns:
        Média arredondada em 2 casas, ou 0.0 se não houver valores.
    """
    if not valores:
        return 0.0
    return round(sum(valores) / len(valores), 2)


def _percentual(parte: int, total: int) -> float:
    """Percentual seguro: retorna 0.0 quando ``total`` é zero.

    Args:
        parte: Numerador.
        total: Denominador.

    Returns:
        Percentual arredondado em 2 casas.
    """
    if total == 0:
        return 0.0
    return round(parte / total * 100.0, 2)


def _calcular_grupo(
    tarefas: Sequence[Mapping[str, Any]], agora: datetime
) -> dict[str, Any]:
    """Calcula métricas de um grupo de tarefas já validadas.

    Tarefas canceladas contam em ``quantidade`` mas ficam fora dos
    cálculos de tempo e atraso.

    Args:
        tarefas: Tarefas validadas do grupo.
        agora: Instante de referência da análise (UTC).

    Returns:
        Dicionário com quantidade, tempo médio e taxa de atraso.
    """
    ativas = [t for t in tarefas if t["status"] != "cancelada"]
    horas = [
        _horas_de_execucao(t) for t in ativas if t["status"] == "concluida"
    ]
    atrasadas = sum(1 for t in ativas if _esta_em_atraso(t, agora))
    return {
        "quantidade": len(tarefas),
        "tempo_medio_conclusao_horas": _media(horas),
        "taxa_atraso_percentual": _percentual(atrasadas, len(ativas)),
    }


def analyze_tasks(
    tarefas: Sequence[Mapping[str, Any]],
    agora: datetime | None = None,
) -> dict[str, Any]:
    """Analisa uma lista de tarefas e retorna métricas de produtividade.

    Args:
        tarefas: Sequência de tarefas (dicionários) conforme o contrato.
        agora: Instante de referência (UTC) para avaliar prazos vencidos.
            Se omitido, usa o horário UTC atual.

    Returns:
        Dicionário com as chaves ``quantidade_tarefas``,
        ``tempo_medio_conclusao_horas``, ``taxa_atraso_percentual``,
        ``indicadores_por_prioridade`` (contrato da Seção 1.3.2) e os
        contadores ``total_tarefas``, ``total_concluidas`` e
        ``total_pendentes`` exigidos pelo desafio da Fase 2.

    Raises:
        TaskValidationError: Se alguma tarefa for inválida ou se
            ``agora`` não estiver em UTC.
    """
    referencia = agora if agora is not None else datetime.now(timezone.utc)
    _validar_data(referencia, "agora", "-")

    for tarefa in tarefas:
        validate_task(tarefa)

    resumo = _calcular_grupo(tarefas, referencia)
    por_prioridade = {
        prioridade: _calcular_grupo(
            [t for t in tarefas if t["prioridade"] == prioridade], referencia
        )
        for prioridade in PRIORIDADES_VALIDAS
    }
    total_concluidas = sum(1 for t in tarefas if t["status"] == "concluida")
    total_pendentes = sum(
        1 for t in tarefas if t["status"] in ("pendente", "em_andamento")
    )
    logger.info(
        "Análise concluída: %d tarefas, %d concluídas, %d pendentes.",
        len(tarefas),
        total_concluidas,
        total_pendentes,
    )
    return {
        "quantidade_tarefas": len(tarefas),
        "total_tarefas": len(tarefas),
        "total_concluidas": total_concluidas,
        "total_pendentes": total_pendentes,
        "tempo_medio_conclusao_horas": resumo["tempo_medio_conclusao_horas"],
        "taxa_atraso_percentual": resumo["taxa_atraso_percentual"],
        "indicadores_por_prioridade": por_prioridade,
    }
