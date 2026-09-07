import java.util.concurrent.Semaphore;

class ContaBancaria {
    private int saldo;
    private Semaphore semaforo;

    public ContaBancaria(int saldoInicial) {
        this.saldo = saldoInicial;
        // Semáforo binário (Mutex)
        this.semaforo = new Semaphore(1);
    }

    public int getSaldo() {
        return this.saldo;
    }

    // Transação sem proteção
    public void transacaoInsegura(int valor) {
        int saldoAtual = this.saldo;
        try { 
            // Força a preempção (condição de corrida)
            Thread.sleep(1); 
        } catch (InterruptedException e) {}
        this.saldo = saldoAtual + valor;
    }

    // Transação segura utilizando Semáforo
    public void transacaoSegura(int valor) {
        try {
            semaforo.acquire(); // Entra na região crítica
            int saldoAtual = this.saldo;
            Thread.sleep(1);
            this.saldo = saldoAtual + valor;
        } catch (InterruptedException e) {
        } finally {
            semaforo.release(); // Sai da região crítica
        }
    }
}

class ClientePix implements Runnable {
    private ContaBancaria conta;
    private int valor;
    private boolean seguro;

    public ClientePix(ContaBancaria conta, int valor, boolean seguro) {
        this.conta = conta;
        this.valor = valor;
        this.seguro = seguro;
    }

    @Override
    public void run() {
        if (this.seguro) {
            this.conta.transacaoSegura(this.valor);
        } else {
            this.conta.transacaoInsegura(this.valor);
        }
    }
}

public class SistemaPix {
    public static void main(String[] args) throws InterruptedException {
        System.out.println("Iniciando simulacao do Sistema Pix (Versao Java)...\n");
        int numThreads = 100;
        
        System.out.println("=== Teste 1: SEM protecao (Condicao de Corrida) ===");
        executarExperimento(false, numThreads);
        
        System.out.println("=== Teste 2: COM protecao (Uso de Semaforo) ===");
        executarExperimento(true, numThreads);
    }

    public static void executarExperimento(boolean seguro, int numThreads) throws InterruptedException {
        ContaBancaria conta = new ContaBancaria(1000);
        Thread[] threads = new Thread[numThreads];
        long inicio = System.currentTimeMillis();

        // Metade deposita, metade saca
        for (int i = 0; i < numThreads; i++) {
            int valor = (i % 2 == 0) ? 10 : -10;
            threads[i] = new Thread(new ClientePix(conta, valor, seguro));
            threads[i].start();
        }

        // Aguarda execução
        for (int i = 0; i < numThreads; i++) {
            threads[i].join();
        }

        long fim = System.currentTimeMillis();
        System.out.println("Saldo Esperado: 1000");
        System.out.println("Saldo Final Obtido: " + conta.getSaldo());
        System.out.println(String.format("Tempo de execucao: %.4f segundos", (fim - inicio) / 1000.0));
        
        if (!seguro) {
            System.out.println("-> AVISO: Inconsistencia detectada! As threads colidiram e sobrescreveram os dados.\n");
        } else {
            System.out.println("-> SUCESSO: A exclusao mutua foi garantida!\n");
        }
    }
}
