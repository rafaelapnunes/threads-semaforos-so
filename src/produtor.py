"""Thread produtora do experimento."""

import threading

from buffers import ErroDeBuffer, janela_de_preempcao


class Produtor(threading.Thread):
    """Insere `quantidade` itens no buffer compartilhado.

    Cada item e o par (id_produtor, sequencial), unico no experimento
    inteiro: e essa unicidade que permite detectar depois item entregue
    duas vezes ou item sobrescrito.

    Os resultados ficam em atributos da propria thread, lidos apenas
    depois do join(). Nao ha contador compartilhado entre threads, para
    que a instrumentacao nao introduza nenhuma corrida propria.
    """

    def __init__(self, id_produtor, buffer, quantidade):
        super().__init__(name=f"Produtor-{id_produtor}")
        self.id_produtor = id_produtor
        self.buffer = buffer
        self.quantidade = quantidade
        self.inseridos = []
        self.falhas = 0

    def run(self):
        for sequencial in range(self.quantidade):
            item = (self.id_produtor, sequencial)
            try:
                self.buffer.inserir(item)
            except ErroDeBuffer:
                self.falhas += 1
            else:
                self.inseridos.append(item)
            # Toda iteracao termina cedendo a vez: sem isso uma unica thread
            # tenderia a monopolizar a fatia do GIL e as threads quase nao se
            # intercalariam. A instrumentacao e a mesma nas tres variantes.
            janela_de_preempcao()
