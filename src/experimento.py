"""Executa as tres variantes do buffer sob a mesma carga e grava os
resultados em CSV.

Saidas (em resultados/):
    rodadas.csv  uma linha por rodada, com as metricas de corretude
    resumo.csv   uma linha por variante, com medias e taxa de falhas
"""

import argparse
import csv
import os
import statistics
import time
from dataclasses import dataclass

import config
from buffers import BufferCompleto, BufferSemMutex, BufferSoMutex
from consumidor import Consumidor
from produtor import Produtor
from verificacao import COLUNAS_RODADA, apurar


@dataclass(frozen=True)
class Variante:
    codigo: str
    descricao: str
    classe_buffer: type


VARIANTES = (
    Variante("A", "so mutex (sem controle de fluxo)", BufferSoMutex),
    Variante("B", "contadores sem mutex (sem exclusao mutua)", BufferSemMutex),
    Variante("C", "contadores + mutex (solucao completa)", BufferCompleto),
)

COLUNAS_RESUMO = [
    "variante",
    "descricao",
    "rodadas",
    "tempo_medio_s",
    "tempo_desvio_s",
    "rodadas_corretas",
    "rodadas_com_falha",
    "taxa_falhas_pct",
    "media_falhas_insercao",
    "media_falhas_remocao",
    "media_entregas_duplicadas",
    "media_leituras_invalidas",
    "media_itens_perdidos",
]


def executar_rodada(variante):
    """Sobe produtores e consumidores sobre um buffer novo e apura o fim."""
    buffer = variante.classe_buffer(config.CAPACIDADE_BUFFER)
    produtores = [
        Produtor(i, buffer, config.ITENS_POR_PRODUTOR)
        for i in range(config.NUM_PRODUTORES)
    ]
    consumidores = [
        Consumidor(i, buffer, config.ITENS_POR_CONSUMIDOR)
        for i in range(config.NUM_CONSUMIDORES)
    ]
    threads = produtores + consumidores

    inicio = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(config.TIMEOUT_JOIN_S)
    tempo_s = time.perf_counter() - inicio

    travadas = sum(1 for thread in threads if thread.is_alive())
    return apurar(produtores, consumidores, travadas, tempo_s)


def executar_variante(variante, num_rodadas):
    apuracoes = []
    for rodada in range(1, num_rodadas + 1):
        apuracao = executar_rodada(variante)
        apuracoes.append(apuracao)
        print(
            f"  rodada {rodada:02d}: "
            f"inseridos={apuracao.itens_inseridos} "
            f"removidos={apuracao.itens_removidos} "
            f"recusas={apuracao.falhas_insercao + apuracao.falhas_remocao} "
            f"duplicadas={apuracao.entregas_duplicadas} "
            f"perdidos={apuracao.itens_perdidos} "
            f"tempo={apuracao.tempo_s:.4f}s "
            f"{'OK' if apuracao.correta else 'FALHA'}"
        )
    return apuracoes


def _media(apuracoes, atributo):
    return statistics.mean(getattr(a, atributo) for a in apuracoes)


def resumir(variante, apuracoes):
    tempos = [a.tempo_s for a in apuracoes]
    corretas = sum(1 for a in apuracoes if a.correta)
    com_falha = len(apuracoes) - corretas
    return {
        "variante": variante.codigo,
        "descricao": variante.descricao,
        "rodadas": len(apuracoes),
        "tempo_medio_s": f"{statistics.mean(tempos):.6f}",
        "tempo_desvio_s": f"{statistics.stdev(tempos) if len(tempos) > 1 else 0.0:.6f}",
        "rodadas_corretas": corretas,
        "rodadas_com_falha": com_falha,
        "taxa_falhas_pct": f"{100 * com_falha / len(apuracoes):.1f}",
        "media_falhas_insercao": f"{_media(apuracoes, 'falhas_insercao'):.1f}",
        "media_falhas_remocao": f"{_media(apuracoes, 'falhas_remocao'):.1f}",
        "media_entregas_duplicadas": f"{_media(apuracoes, 'entregas_duplicadas'):.1f}",
        "media_leituras_invalidas": f"{_media(apuracoes, 'leituras_invalidas'):.1f}",
        "media_itens_perdidos": f"{_media(apuracoes, 'itens_perdidos'):.1f}",
    }


def gravar_csv(caminho, colunas, linhas):
    with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"gravado: {caminho}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--variantes",
        nargs="+",
        choices=[v.codigo for v in VARIANTES],
        default=[v.codigo for v in VARIANTES],
        help="variantes a executar (padrao: todas)",
    )
    parser.add_argument(
        "--rodadas",
        type=int,
        default=config.NUM_RODADAS,
        help=f"rodadas por variante (padrao: {config.NUM_RODADAS})",
    )
    argumentos = parser.parse_args()

    print(
        f"{config.NUM_PRODUTORES} produtores x {config.ITENS_POR_PRODUTOR} itens, "
        f"{config.NUM_CONSUMIDORES} consumidores x {config.ITENS_POR_CONSUMIDOR} itens, "
        f"buffer de {config.CAPACIDADE_BUFFER} posicoes, "
        f"{argumentos.rodadas} rodadas por variante.\n"
    )

    linhas_rodadas = []
    linhas_resumo = []
    for variante in VARIANTES:
        if variante.codigo not in argumentos.variantes:
            continue
        print(f"Variante {variante.codigo} - {variante.descricao}")
        apuracoes = executar_variante(variante, argumentos.rodadas)
        for rodada, apuracao in enumerate(apuracoes, start=1):
            linha = {"variante": variante.codigo, "rodada": rodada}
            linha.update(apuracao.como_linha_csv())
            linhas_rodadas.append(linha)
        linhas_resumo.append(resumir(variante, apuracoes))
        print()

    os.makedirs(config.DIRETORIO_RESULTADOS, exist_ok=True)
    gravar_csv(config.CSV_RODADAS, ["variante", "rodada"] + COLUNAS_RODADA, linhas_rodadas)
    gravar_csv(config.CSV_RESUMO, COLUNAS_RESUMO, linhas_resumo)


if __name__ == "__main__":
    main()
