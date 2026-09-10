"""As tres variantes do buffer circular compartilhado.

Todas expoem a mesma interface (inserir/remover) e a mesma estrutura
interna; o que muda de uma para outra e apenas o mecanismo de
sincronizacao, de modo que cada variante isole uma dimensao do problema:

    BufferSoMutex   exclusao mutua, sem controle de fluxo
    BufferSemMutex  controle de fluxo, sem exclusao mutua
    BufferCompleto  as duas coisas (solucao classica de Dijkstra)
"""

import threading
import time


class ErroDeBuffer(RuntimeError):
    """Base das falhas de controle de fluxo (buffer cheio ou vazio)."""


class BufferCheio(ErroDeBuffer):
    pass


class BufferVazio(ErroDeBuffer):
    pass


def janela_de_preempcao():
    """Forca o interpretador a considerar uma troca de thread aqui.

    O escalonador do SO pode preemptar uma thread em qualquer ponto, mas
    numa secao critica de poucos bytecodes isso raramente acontece sob o
    GIL do CPython — a corrida existiria e simplesmente nao seria
    observada. Esta chamada torna o pior caso reprodutivel; ela e
    executada por todas as variantes, no mesmo ponto, para que a
    comparacao entre elas continue valida.
    """
    time.sleep(0)


class BufferCircular:
    """Estado compartilhado comum: vetor pre-alocado e os dois indices.

    As subclasses definem a sincronizacao em torno de _escrever/_ler.
    """

    def __init__(self, capacidade):
        self.capacidade = capacidade
        self._vetor = [None] * capacidade
        self._indice_escrita = 0
        self._indice_leitura = 0

    def _escrever(self, item):
        """Secao critica de escrita: le o indice, grava, avanca o indice."""
        indice = self._indice_escrita
        janela_de_preempcao()
        self._vetor[indice] = item
        self._indice_escrita = (indice + 1) % self.capacidade

    def _ler(self):
        """Secao critica de leitura, simetrica a _escrever."""
        indice = self._indice_leitura
        janela_de_preempcao()
        item = self._vetor[indice]
        self._indice_leitura = (indice + 1) % self.capacidade
        return item

    def inserir(self, item):
        raise NotImplementedError

    def remover(self):
        raise NotImplementedError


class BufferSoMutex(BufferCircular):
    """Variante A: exclusao mutua garantida, sem controle de fluxo.

    Um semaforo binario serializa a secao critica, entao o estado interno
    nunca se corrompe. Falta, porem, a sincronizacao por condicao: quem
    encontra o buffer cheio (ou vazio) recebe um erro em vez de esperar, e
    o item e descartado. Mostra que exclusao mutua sozinha nao basta.
    """

    def __init__(self, capacidade):
        super().__init__(capacidade)
        self._quantidade = 0
        self._mutex = threading.Semaphore(1)

    def inserir(self, item):
        self._mutex.acquire()
        try:
            if self._quantidade >= self.capacidade:
                raise BufferCheio("buffer cheio")
            self._escrever(item)
            self._quantidade += 1
        finally:
            self._mutex.release()

    def remover(self):
        self._mutex.acquire()
        try:
            if self._quantidade <= 0:
                raise BufferVazio("buffer vazio")
            item = self._ler()
            self._quantidade -= 1
            return item
        finally:
            self._mutex.release()


class BufferComContadores(BufferCircular):
    """Base das variantes B e C: controle de fluxo por semaforos contadores.

    `vazio` conta posicoes livres e comeca em `capacidade`; `cheio` conta
    itens prontos e comeca em zero. O produtor reserva uma posicao livre
    antes de escrever e sinaliza um item pronto depois; o consumidor faz o
    inverso. Nenhuma das duas pontas prossegue sobre um buffer cheio ou
    vazio: elas bloqueiam. Esta classe nao define exclusao mutua.
    """

    def __init__(self, capacidade):
        super().__init__(capacidade)
        self._vazio = threading.Semaphore(capacidade)
        self._cheio = threading.Semaphore(0)


class BufferSemMutex(BufferComContadores):
    """Variante B: controle de fluxo correto, sem exclusao mutua.

    Nenhum produtor tenta escrever em buffer cheio nem consumidor ler de
    buffer vazio, mas nada impede que duas threads executem a secao
    critica ao mesmo tempo: elas podem ler o mesmo indice e uma sobrescrever
    o item da outra (perda) ou entregar o mesmo item duas vezes (duplicata).
    """

    def inserir(self, item):
        self._vazio.acquire()
        self._escrever(item)      # secao critica desprotegida
        self._cheio.release()

    def remover(self):
        self._cheio.acquire()
        item = self._ler()        # secao critica desprotegida
        self._vazio.release()
        return item


class BufferCompleto(BufferComContadores):
    """Variante C: solucao classica com tres semaforos.

    Identica a variante B, mais um semaforo binario `mutex` em volta da
    secao critica. E a unica diferenca entre as duas — o que isola a
    exclusao mutua como causa das falhas observadas na variante B.
    """

    def __init__(self, capacidade):
        super().__init__(capacidade)
        self._mutex = threading.Semaphore(1)

    def inserir(self, item):
        self._vazio.acquire()     # espera uma posicao livre
        self._mutex.acquire()     # entra na secao critica
        self._escrever(item)
        self._mutex.release()
        self._cheio.release()     # sinaliza um item pronto

    def remover(self):
        self._cheio.acquire()     # espera um item pronto
        self._mutex.acquire()
        item = self._ler()
        self._mutex.release()
        self._vazio.release()     # devolve a posicao ao buffer
        return item
