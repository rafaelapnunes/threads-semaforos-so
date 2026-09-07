# Relatório do Trabalho: Threads e Semáforos no SO

## 1. Descrição da Aplicação
O problema escolhido para demonstrar o conceito de condição de corrida (Race Condition) e o uso de Semáforos para Exclusão Mútua foi o do **Sistema Pix (Entrada e Saída de Saldo)**. 

A aplicação consiste em uma representação simples de uma conta bancária (`ContaBancaria`) que possui um saldo inicial e recebe múltiplas transações concorrentes (depósitos e saques) através de diferentes _threads_. Em um ambiente multiprocessado, como essas operações envolvem a leitura, modificação e escrita do saldo (uma variável compartilhada), elas são suscetíveis à preempção pelo Sistema Operacional. Sem um mecanismo de controle de concorrência, ocorre a inconsistência de dados.

O código foi implementado em **Python** e também em **Java** (conforme sugerido), fazendo uso de `threading.Semaphore` no Python e `java.util.concurrent.Semaphore` no Java, ambos inicializados com o valor `1` (funcionando como um semáforo binário / _mutex_) para garantir a exclusão mútua na seção crítica.

## 2. Teste Implementado
A execução do teste consiste em instanciar `100` _threads_. Metade dessas _threads_ realiza operações de depósito (R$ 10) e a outra metade realiza saques (R$ 10). Ao final de todas as transações, espera-se que o saldo retorne ao seu valor original (R$ 1000,00). 

Para provar a falta de exclusão mútua e também sua correção, os scripts executam dois experimentos:
1. **Transação Insegura:** O programa apenas lê e atualiza a variável global, introduzindo um pequeno atraso (`sleep` de 1 milissegundo) para simular o tempo de processamento/I.O. e provocar a preempção (troca de contexto) entre as _threads_.
2. **Transação Segura:** O programa utiliza as funções `acquire()` e `release()` de um semáforo antes e depois das operações de atualização de saldo.

Adicionalmente, foi incluído um arquivo de Teste Unitário automatizado (`test_sistema.py`) que usa o módulo `unittest` do Python para garantir matematicamente e repetidamente que a versão com Semáforo funciona e a sem proteção falha.

## 3. Execução do Experimento
Tanto na versão Python quanto na versão Java, os resultados são análogos:

### Sem Proteção (Condição de Corrida)
* **Saldo Esperado:** 1000
* **Saldo Final Obtido:** Variável a cada execução (ex: 990, 1020, 950, etc.).
* **Tempo de Execução:** Menor
* **Análise:** Muitas _threads_ leem o saldo antigo simultaneamente e o sobrescrevem, causando a perda de transações no processo. O saldo final não bate com o esperado, provando a ausência de exclusão mútua.

### Com Proteção (Uso de Semáforo)
* **Saldo Esperado:** 1000
* **Saldo Final Obtido:** 1000 (Consistente e exato)
* **Tempo de Execução:** Maior
* **Análise:** O semáforo permitiu que apenas uma _thread_ por vez manipulasse o saldo da conta. O resultado foi mantido consistente. O tempo de execução sofreu um acréscimo justificado pelo tempo em que as _threads_ ficaram bloqueadas aguardando a liberação do semáforo.

## Como executar
Para maior conveniência, os arquivos `.bat` (Windows) e `.sh` (Linux/Mac) foram disponibilizados.

**No Windows (Terminal, CMD ou PowerShell):**
```cmd
.\rodar_teste.bat
```

**No Linux / Mac:**
```bash
chmod +x rodar_teste.sh
./rodar_teste.sh
```

Ou execute os arquivos individualmente:
* `python sistema_pix.py`
* `python -m unittest test_sistema.py`
* `javac SistemaPix.java` e `java SistemaPix`