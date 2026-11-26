# Etapa 2 — Versão OpenMP (memória compartilhada)

**Responsável:** Carlos Eduardo

Código: `openmp/01_matmul_omp.cpp` (as justificativas também estão no cabeçalho do arquivo).

## Padrão escolhido

`#pragma omp parallel for` no **laço externo `i`**. Cada iteração calcula uma
linha inteira de C, e linhas diferentes são independentes. Paralelizar o laço
externo cria a região paralela uma vez só e dá a cada thread um pedaço grande de
trabalho (N² operações por linha). Seções ou tasks não se aplicam: o trabalho é
um laço regular, não blocos heterogêneos nem recursão.

## Condições de corrida

**Não há** no laço principal:

- cada thread escreve só nas linhas de C que recebeu;
- A e B são somente lidas;
- `i` é privada (variável do `parallel for`); `k`, `j` e `a` são declaradas dentro
  do laço, logo privadas.

Por isso **não usamos critical, atomic nem reduction** no cálculo: só
acrescentariam sincronização. Contraexemplo: paralelizar o laço `k` faria várias
threads somarem no mesmo `C[i][j]` → corrida, exigindo atomic (N³ operações
atômicas, lentíssimo) ou reduction.

O **checksum** fica sequencial de propósito: `reduction(+:soma)` mudaria a ordem das
somas em ponto flutuante (que não é associativo) e o resultado poderia divergir nas
últimas casas. Ele é O(N²), desprezível perto do O(N³).

## Resultado idêntico ao baseline

Cada `C[i][j]` continua acumulando `k = 0, 1, …, N−1` na mesma ordem do sequencial;
só muda **qual thread** faz a linha. Logo o checksum é idêntico bit a bit
(conferido automaticamente em todas as medições — coluna `valido` dos CSVs).

## `__restrict`

Sem os ponteiros `__restrict`, o compilador não consegue provar que A, B e C não se
sobrepõem dentro da região paralela e deixa de vetorizar o laço `j`: com 1 thread a
versão OpenMP ficava mais lenta que o baseline. Com eles, volta a vetorizar. Não
muda a ordem das operações.

## Escalonamento

Escolhido: **`schedule(static)`**. A matriz é densa, então toda linha custa
exatamente N² multiplicações: não há desbalanceamento a corrigir.

- `static`: blocos contíguos de N/p linhas, divididos uma vez, sem custo em tempo de
  execução. Cada thread escreve numa faixa contígua de C → pouco *false sharing*.
- `dynamic`: as threads pegam pedaços de uma fila compartilhada durante a execução →
  overhead de sincronização, sem benefício com carga uniforme. Com `chunk = 1`,
  linhas vizinhas vão para threads diferentes (pior localidade).
- `guided`: pedaços que diminuem com o tempo; meio-termo, também sem vantagem aqui.

Medição: `scripts/medir_escalonamento.sh` → `results/escalonamento.csv`,
`results/escalonamento.png` e `results/resumo.md` (seção 5). `dynamic` só
compensaria num problema com carga desigual, como o Mandelbrot.

## Curva de speedup

`results/speedup.png`, `results/eficiencia.png` e `results/resumo.md` (seção 3).

**Por que a curva satura:**

1. **Banda de memória.** Com matrizes grandes, os núcleos passam a esperar a RAM;
   dobrar threads não dobra a banda.
2. **Núcleos físicos.** Acima do número de núcleos físicos (hyperthreading), as
   threads dividem as mesmas unidades de cálculo.
3. **N pequeno.** O trabalho por thread é tão curto que o custo de criar e
   sincronizar a equipe de threads pesa.
