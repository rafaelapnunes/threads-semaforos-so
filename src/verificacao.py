"""Apuracao de uma rodada: transforma o que as threads registraram em
metricas de corretude.

O criterio e comparar o multiconjunto de itens efetivamente inseridos com
o de itens entregues aos consumidores. Numa execucao correta os dois
coincidem, a menos dos itens que ainda estejam no buffer no fim.
"""

from collections import Counter
from dataclasses import dataclass, fields


@dataclass(frozen=True)
class Apuracao:
    """Resultado de uma rodada.

    Falhas de controle de fluxo (insercao/remocao recusada) e violacoes de
    exclusao mutua (duplicata, leitura invalida, perda) sao contadas
    separadamente: e essa separacao que permite atribuir cada falha ao
    mecanismo de sincronizacao que esta faltando.
    """

    tempo_s: float
    itens_inseridos: int
    itens_removidos: int
    falhas_insercao: int
    falhas_remocao: int
    entregas_duplicadas: int
    leituras_invalidas: int
    itens_perdidos: int
    threads_travadas: int

    @property
    def violou_controle_fluxo(self):
        return self.falhas_insercao > 0 or self.falhas_remocao > 0

    @property
    def violou_exclusao_mutua(self):
        return (
            self.entregas_duplicadas > 0
            or self.leituras_invalidas > 0
            or self.itens_perdidos > 0
        )

    @property
    def correta(self):
        return not (
            self.violou_controle_fluxo
            or self.violou_exclusao_mutua
            or self.threads_travadas > 0
        )

    def como_linha_csv(self):
        linha = {campo.name: getattr(self, campo.name) for campo in fields(self)}
        linha["tempo_s"] = f"{self.tempo_s:.6f}"
        linha["violou_controle_fluxo"] = int(self.violou_controle_fluxo)
        linha["violou_exclusao_mutua"] = int(self.violou_exclusao_mutua)
        linha["correta"] = int(self.correta)
        return linha


COLUNAS_RODADA = [campo.name for campo in fields(Apuracao)] + [
    "violou_controle_fluxo",
    "violou_exclusao_mutua",
    "correta",
]


def apurar(produtores, consumidores, threads_travadas, tempo_s):
    """Consolida os registros das threads em uma Apuracao."""
    inseridos = [item for p in produtores for item in p.inseridos]
    removidos = [item for c in consumidores for item in c.removidos]

    contagem_removidos = Counter(removidos)
    # None so pode aparecer se alguem leu uma posicao ainda nao escrita.
    leituras_invalidas = contagem_removidos.pop(None, 0)
    entregas_duplicadas = sum(
        vezes - 1 for vezes in contagem_removidos.values() if vezes > 1
    )

    # Itens inseridos que nunca chegaram a um consumidor. Parte deles pode
    # legitimamente ter sobrado no buffer, entao essa sobra e descontada;
    # o que resta foi sobrescrito por outra thread.
    nao_entregues = sum((Counter(inseridos) - contagem_removidos).values())
    sobra_no_buffer = max(len(inseridos) - len(removidos), 0)
    itens_perdidos = max(nao_entregues - sobra_no_buffer, 0)

    return Apuracao(
        tempo_s=tempo_s,
        itens_inseridos=len(inseridos),
        itens_removidos=len(removidos),
        falhas_insercao=sum(p.falhas for p in produtores),
        falhas_remocao=sum(c.falhas for c in consumidores),
        entregas_duplicadas=entregas_duplicadas,
        leituras_invalidas=leituras_invalidas,
        itens_perdidos=itens_perdidos,
        threads_travadas=threads_travadas,
    )
