# Produtor-Consumidor com Buffer Limitado — Threads e Semáforos

Trabalho 1 da disciplina de Sistemas Operacionais. O enunciado pede um programa concorrente com threads e semáforos que **prove, em execução, que o código não garante exclusão mútua e que ela passa a ser garantida depois da introdução dos semáforos**, medindo também o tempo de execução em cada condição. A linguagem e o problema são de livre escolha; aqui a escolha foi Python 3 (`threading`) e o problema do produtor-consumidor com buffer limitado, o mesmo para o qual Dijkstra propôs os semáforos.

## O problema

Threads *produtoras* geram itens e os depositam em um buffer circular de capacidade fixa; threads *consumidoras* retiram esses itens do mesmo buffer. O problema foi escolhido porque exige **duas** formas de sincronização ao mesmo tempo, e não uma:

- **exclusão mútua** sobre o vetor e os índices do buffer, para que duas threads não manipulem a mesma posição simultaneamente — resolvida por um semáforo binário;
- **sincronização por condição**, para que o produtor *espere* quando o buffer está cheio e o consumidor *espere* quando está vazio — resolvida por semáforos contadores, e inexpressável com um mutex simples, que não tem contagem.

É essa segunda dimensão que faz do produtor-consumidor um problema cuja corretude depende de semáforos, e não apenas de exclusão mútua, como o enunciado pede.

## O desenho: três variantes, não duas

O desenho intuitivo seria comparar duas versões — "sem nada" contra "com semáforos" — e mostrar que a primeira falha. Esse desenho não prova nada sobre exclusão mútua: as duas versões diferem em *duas* coisas ao mesmo tempo, porque a versão insegura normalmente também perde o controle de fluxo (estoura o buffer ou recusa itens quando ele está cheio). Quando ela falha, a explicação mais simples é a outra, e não a ausência de exclusão mútua.

Por isso o experimento implementa **três** variantes do mesmo buffer, com a mesma interface e a mesma estrutura interna, removendo **um** mecanismo por vez:

| Variante | Exclusão mútua | Controle de fluxo | O que demonstra |
|---|---|---|---|
| **A** `BufferSoMutex` | sim (`mutex`) | não (recusa em vez de esperar) | exclusão mútua **não basta**: nada se corrompe, mas um terço dos itens é descartado |
| **B** `BufferSemMutex` | **não** | sim (`vazio`/`cheio`) | exclusão mútua é **necessária**: 52% das entregas saem duplicadas ou perdidas |
| **C** `BufferCompleto` | sim (`mutex`) | sim (`vazio`/`cheio`) | solução clássica com três semáforos: correta em 10/10 rodadas |

As variantes B e C são a comparação decisiva: herdam da mesma classe base, têm o mesmo controle de fluxo e diferem **exclusivamente** pela presença do `mutex` em volta da seção crítica, então qualquer divergência entre as duas é atribuível à exclusão mútua e a nada mais. A variante A cobre o outro lado do argumento: tem exclusão mútua perfeita e ainda assim falha.

## Estrutura do repositório

```
src/
  config.py        parametros do experimento e caminhos de saida
  buffers.py       classe base do buffer circular + as tres variantes
  produtor.py      thread produtora
  consumidor.py    thread consumidora
  verificacao.py   apuracao de uma rodada e metricas de corretude
  experimento.py   execucao das variantes e geracao dos CSVs

resultados/
  rodadas.csv      uma linha por rodada (30 rodadas), com todas as metricas
  resumo.csv       uma linha por variante, com medias e taxa de falhas

relatorio.md       relatorio do trabalho
```

| Módulo | Responsabilidade |
|---|---|
| `config.py` | todos os parâmetros do experimento em um só lugar (capacidade do buffer, número de threads, itens por thread, rodadas, timeout) e os caminhos dos CSVs. Importado pelos demais módulos, o que garante que as três variantes rodem sempre sob carga idêntica |
| `buffers.py` | `BufferCircular` (estado compartilhado e as duas seções críticas), `BufferComContadores` (os semáforos `vazio` e `cheio`, base de B e C) e as três variantes `BufferSoMutex`, `BufferSemMutex` e `BufferCompleto`. Também define `janela_de_preempcao()` e as exceções de fluxo `BufferCheio`/`BufferVazio` |
| `produtor.py` | `Produtor(threading.Thread)`: insere itens `(id_produtor, sequencial)`, únicos no experimento inteiro, e registra o que inseriu e o que foi recusado |
| `consumidor.py` | `Consumidor(threading.Thread)`: simétrico, registra o que recebeu — inclusive `None`, que denuncia leitura de posição nunca escrita |
| `verificacao.py` | a dataclass `Apuracao` e a função `apurar()`, que comparam o multiconjunto de itens inseridos com o de itens entregues e derivam as métricas de corretude |
| `experimento.py` | ponto de entrada: executa as rodadas de cada variante, imprime o progresso e grava os dois CSVs. Aceita `--variantes` e `--rodadas` |

Nenhuma estrutura de alto nível já sincronizada (`queue.Queue`, `Condition`, `Lock`) é utilizada: todo o controle de concorrência é feito explicitamente com `threading.Semaphore`, para que o papel de cada semáforo fique visível.

## Como o experimento foi executado

Cada **rodada** cria um buffer novo e threads novas, inicia todas de uma vez, espera com `join()` e apura o resultado. Os parâmetros, em `config.py` e idênticos para as três variantes, foram:

- capacidade do buffer: **10** posições;
- **4** threads produtoras × **1000** itens = **4000** itens a inserir;
- **4** threads consumidoras × **1000** itens = **4000** itens a remover;
- **10** rodadas independentes por variante, ou seja, 30 rodadas no total;
- `timeout` de 30 s no `join()`, como rede de segurança contra travamento.

A carga é balanceada de propósito — o total que os consumidores tentam remover é igual ao total que os produtores tentam inserir — de modo que, numa execução correta, o buffer termina vazio e qualquer sobra já é sintoma de erro.

O tempo é medido com `time.perf_counter()`, do `start()` da primeira thread ao `join()` da última. Não há nenhum `sleep` de duração arbitrária no laço das threads: um atraso de milissegundos por iteração dominaria a medição e tornaria a comparação de tempo um artefato do próprio atraso, e não do custo de sincronização.

Ambiente da execução publicada: CPython **3.13.9** em Windows 11 (10.0.26200), Intel64 Family 6 Model 140 (Intel Core de 11ª geração), 8 núcleos lógicos, intervalo de troca de threads no padrão de 5 ms.

Comandos:

```bash
python src/experimento.py                    # todas as variantes, 10 rodadas cada
python src/experimento.py --variantes B C    # apenas a comparação decisiva
python src/experimento.py --rodadas 3        # menos rodadas
```

Requer apenas Python 3, sem dependências externas. Cada execução reescreve os dois CSVs, inclusive as parciais — os resultados publicados abaixo vêm da execução completa, sem argumentos.

## Critério de corretude

Como cada item é único, a execução pode ser verificada comparando o multiconjunto de itens inseridos com o de itens entregues aos consumidores. Uma rodada só é considerada correta se as seis métricas abaixo forem zero:

| Métrica | Significado | Aponta para |
|---|---|---|
| `falhas_insercao` | inserções recusadas (buffer cheio) | falta de controle de fluxo |
| `falhas_remocao` | remoções recusadas (buffer vazio) | falta de controle de fluxo |
| `entregas_duplicadas` | mesmo item entregue a mais de um consumidor | falta de exclusão mútua |
| `leituras_invalidas` | leitura de posição nunca escrita (`None`) | falta de exclusão mútua |
| `itens_perdidos` | item inserido, nunca entregue e ausente do buffer (sobrescrito) | falta de exclusão mútua |
| `threads_travadas` | threads vivas depois do `join()` com timeout | *deadlock* / *livelock* |

A separação entre falhas de fluxo e violações de exclusão mútua é o que permite atribuir cada falha ao mecanismo que está faltando.

## Resultados obtidos

| Variante | Tempo médio (s) | Desvio (s) | Rodadas corretas | Recusas ins./rem. (méd.) | Duplicadas (méd.) | Perdidos (méd.) |
|---|---|---|---|---|---|---|
| **A** só mutex | 0,0823 | 0,0132 | 0/10 | 1286,3 / 1288,4 | 0,0 | 0,0 |
| **B** sem mutex | 0,0690 | 0,0011 | 0/10 | 0,0 / 0,0 | 2076,3 | 2076,3 |
| **C** completa | 0,1285 | 0,0034 | **10/10** | 0,0 / 0,0 | 0,0 | 0,0 |

As duas provas que o enunciado pede ficam separadas e cada uma limpa. A variante A tem exclusão mútua perfeita — zero itens duplicados ou perdidos em 10 rodadas — e ainda assim descarta 32% dos itens, porque sem contagem não há como fazer o produtor esperar: um mutex resolve metade do problema. A variante B tem controle de fluxo perfeito — 4000 inserções e 4000 remoções, zero recusas, zero travamentos — e corrompe 52% das entregas, com itens entregues duas vezes e itens sobrescritos antes de serem lidos: é a violação de exclusão mútua isolada de qualquer outra causa. A variante C acerta as 10 rodadas.

O overhead de sincronização, medido entre B e C (as duas variantes que só diferem pelo `mutex`), é de **+86%** no tempo de execução. O tempo da variante A não é comparável, porque ela executou apenas dois terços do trabalho — e seu desvio padrão, muito maior que os outros dois, mostra o quanto o resultado dela depende da sorte do escalonamento.

## Nota sobre o GIL

A seção crítica das três variantes contém uma chamada a `janela_de_preempcao()` (`time.sleep(0)`), que força o interpretador a considerar uma troca de thread naquele ponto. A corrida da variante B existe com ou sem essa chamada, mas sob o GIL do CPython o intervalo de troca é de 5 ms — tempo em que uma thread executa milhares de bytecodes — e a preempção raramente cai dentro de uma seção crítica tão curta. Num experimento de controle, sem a janela, a variante B completou as 4000 operações sem nenhuma divergência observável, apesar de não ter proteção alguma. A janela não cria o defeito: ela torna reprodutível o pior caso que o escalonador poderia produzir a qualquer momento, e é executada pelas três variantes, no mesmo ponto, preservando a validade da comparação.

O relatório completo do trabalho, com a discussão desse ponto e das demais conclusões, está em [`relatorio.md`](relatorio.md).
