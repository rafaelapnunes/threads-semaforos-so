"""Thread consumidora do experimento."""

import threading

from buffers import ErroDeBuffer, janela_de_preempcao


class Consumidor(threading.Thread):
    """Remove `quantidade` itens do buffer compartilhado.

    Simetrica ao Produtor: guarda em `removidos` cada item efetivamente
    entregue pelo buffer — inclusive None, que denuncia leitura de uma
    posicao nunca escrita — e conta em `falhas` as remocoes recusadas.
    """

    def __init__(self, id_consumidor, buffer, quantidade):
        super().__init__(name=f"Consumidor-{id_consumidor}")
        self.id_consumidor = id_consumidor
        self.buffer = buffer
        self.quantidade = quantidade
        self.removidos = []
        self.falhas = 0

    def run(self):
        for _ in range(self.quantidade):
            try:
                item = self.buffer.remover()
            except ErroDeBuffer:
                self.falhas += 1
            else:
                self.removidos.append(item)
            janela_de_preempcao()  # ver comentario em Produtor.run
