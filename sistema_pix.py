import threading
import time

class ContaBancaria:
    def __init__(self, saldo_inicial=0):
        self.saldo = saldo_inicial
        # Semáforo binário iniciado com 1, funcionando para garantir exclusão mútua
        self.semaforo = threading.Semaphore(1)
        
    def transacao_insegura(self, valor):
        """
        Realiza uma transação (soma ou subtração) sem proteção.
        A pausa de 1ms simula uma operação de I/O (ex: acesso a banco de dados)
        forçando a troca de contexto entre as threads.
        """
        saldo_atual = self.saldo
        time.sleep(0.001) # Força a preempção (condição de corrida)
        self.saldo = saldo_atual + valor
        
    def transacao_segura(self, valor):
        """
        Realiza uma transação com proteção utilizando Semáforo.
        Garante a exclusão mútua na seção crítica.
        """
        self.semaforo.acquire()
        try:
            saldo_atual = self.saldo
            time.sleep(0.001)
            self.saldo = saldo_atual + valor
        finally:
            self.semaforo.release()

def executar_experimento(seguro, num_threads=100):
    conta = ContaBancaria(1000)
    threads = []

    # Metade das threads vai depositar R$ 10 e a outra metade vai sacar R$ 10.
    # O saldo final esperado ao fim de todas as transações é R$ 1000.
    
    inicio = time.time()
    
    for i in range(num_threads):
        valor = 10 if i % 2 == 0 else -10
        if seguro:
            t = threading.Thread(target=conta.transacao_segura, args=(valor,))
        else:
            t = threading.Thread(target=conta.transacao_insegura, args=(valor,))
        threads.append(t)
        t.start()
        
    # Aguarda todas as threads finalizarem
    for t in threads:
        t.join()
        
    fim = time.time()
    tempo_execucao = fim - inicio
    
    return conta.saldo, tempo_execucao

if __name__ == "__main__":
    print("Iniciando simulação do Sistema Pix...\n")
    
    # Execução sem semáforo
    print("=== Teste 1: SEM proteção (Condição de Corrida) ===")
    saldo_final_inseguro, tempo_inseguro = executar_experimento(seguro=False)
    print(f"Saldo Esperado: 1000")
    print(f"Saldo Final Obtido: {saldo_final_inseguro}")
    print(f"Tempo de execução: {tempo_inseguro:.4f} segundos")
    if saldo_final_inseguro != 1000:
        print("-> AVISO: Inconsistência detectada! As threads sobrescreveram os valores umas das outras.\n")
    else:
        print("-> Saldo correto (embora inseguro, as threads por sorte não colidiram).\n")

    # Execução com semáforo
    print("=== Teste 2: COM proteção (Uso de Semáforo) ===")
    saldo_final_seguro, tempo_seguro = executar_experimento(seguro=True)
    print(f"Saldo Esperado: 1000")
    print(f"Saldo Final Obtido: {saldo_final_seguro}")
    print(f"Tempo de execução: {tempo_seguro:.4f} segundos")
    if saldo_final_seguro == 1000:
        print("-> SUCESSO: A exclusão mútua foi garantida. O saldo está consistente!\n")
    else:
        print("-> ERRO: Ocorreu um problema inesperado.\n")
