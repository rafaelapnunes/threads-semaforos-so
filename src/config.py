"""Parametros do experimento, centralizados para que as tres variantes
sejam sempre comparadas sob exatamente a mesma carga de trabalho."""

import os

# Posicoes do buffer circular compartilhado.
CAPACIDADE_BUFFER = 10

NUM_PRODUTORES = 4
NUM_CONSUMIDORES = 4

# Itens que cada produtor tenta inserir.
ITENS_POR_PRODUTOR = 1000

# Rodadas independentes por variante (cada rodada recria buffer e threads).
NUM_RODADAS = 10

# Rede de seguranca do join(): uma variante incorreta pode travar threads.
TIMEOUT_JOIN_S = 30.0

ITENS_TOTAIS = NUM_PRODUTORES * ITENS_POR_PRODUTOR

# A carga e balanceada de proposito: o total que os consumidores tentam
# remover e igual ao total que os produtores tentam inserir. Assim, numa
# execucao correta o buffer termina vazio e qualquer sobra e sintoma de erro.
if ITENS_TOTAIS % NUM_CONSUMIDORES != 0:
    raise ValueError(
        "ITENS_TOTAIS deve ser divisivel por NUM_CONSUMIDORES para que a "
        "carga fique balanceada"
    )
ITENS_POR_CONSUMIDOR = ITENS_TOTAIS // NUM_CONSUMIDORES

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRETORIO_RESULTADOS = os.path.join(_RAIZ, "resultados")
CSV_RODADAS = os.path.join(DIRETORIO_RESULTADOS, "rodadas.csv")
CSV_RESUMO = os.path.join(DIRETORIO_RESULTADOS, "resumo.csv")
