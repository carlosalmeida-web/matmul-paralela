# Etapa 1 — Baseline e Perfilamento

**Responsável:** Yasmim Ferreira

## O que o programa faz

Calcula `C = A × B` para matrizes **densas** N×N de `double` (todos os N² elementos
são armazenados e todas as contas são feitas, inclusive com zeros). As matrizes são
guardadas "achatadas" em um vetor, linha após linha (*row-major*): o elemento
`(i, j)` fica na posição `i*N + j`.

Cada elemento é `C[i][j] = Σₖ A[i][k] · B[k][j]`. O código usa a ordem de laços
**i-k-j** em vez da ingênua i-j-k: no laço mais interno (`j`), `B[k*N + j]` e
`C[i*N + j]` são lidos em posições **consecutivas** da memória, o que aproveita o
cache (cada linha de cache traz 8 doubles vizinhos) e permite ao compilador
vetorizar o laço (SIMD). A ordem i-j-k percorreria a coluna de B, pulando N
posições a cada passo.

A entrada é determinística (`A[i] = (i % 100)·0,01`, `B[i] = ((i·7) % 100)·0,01`)
e o **checksum** (soma de todos os elementos de C) é o gabarito de corretude das
versões paralelas.

## Complexidade

| Trecho | Complexidade | Paralelizado? |
|---|---|---|
| Alocação (os `vector` zeram a memória) | O(N²) | não |
| Inicialização de A e B | O(N²) | não |
| **Multiplicação (laço triplo)** | **O(N³)** — 2N³ operações de ponto flutuante | **sim** |
| Checksum | O(N²) | não (mantido sequencial para não mudar a ordem das somas) |

Memória: 3 matrizes × N² × 8 bytes. Ex.: N = 1024 → 24 MB; N = 1536 → 54 MB.

## Perfilamento

Ferramenta: cópia instrumentada `sequential/01_matmul_profile.cpp`, com a mesma
lógica e entrada do baseline e um cronômetro (`clock_gettime(CLOCK_MONOTONIC)`)
em volta de cada trecho. Não usamos `gprof` porque ele mede tempo **por função**,
e todo o trabalho está dentro do `main` — ele só diria "100% no main".

Resultados: **`results/resumo.md`, seção 1** (gerado a partir de `results/perfil.csv`).

**Hotspot:** a multiplicação, com mais de 90% do tempo, e a fatia cresce com N,
porque ela é O(N³) e o resto é O(N²): ao dobrar N, a multiplicação fica ~8× mais
lenta e os outros trechos ~4×.

## Protocolo de medição

- 6 execuções por configuração; a **1ª é aquecimento** e é descartada (memória e
  caches ainda "frios").
- **Mediana** das 5 restantes (robusta a uma execução atrapalhada pelo sistema).
- Tamanhos: N = 512, 1024 e 1536 (padrão; configuráveis em `NS`).
- Compilação com `-O2`, igual para todas as versões.
- Máquina, compilador e parâmetros ficam registrados em `results/maquina.txt`.
- Tudo automatizado em `scripts/medir.sh` (`make medir`).

## Lei de Amdahl

Fração paralelizável **f** = tempo da multiplicação / tempo total do baseline.

- Speedup previsto com p núcleos: **S(p) = 1 / ((1 − f) + f/p)**
- Speedup máximo (p → ∞): **S_max = 1 / (1 − f)**

Os valores de f e S_max para cada N estão em `results/resumo.md` (seção 1), e a
comparação entre o previsto e o medido em `results/amdahl.png`.

Como f aumenta com N, **matrizes maiores escalam melhor**: a parte sequencial
vira uma fatia cada vez menor do total.

## Por que o medido fica abaixo de Amdahl

Amdahl supõe que a parte paralela divide perfeitamente por p. Na prática:

- **Banda de memória:** todos os núcleos disputam o mesmo barramento até a RAM.
  Quando as matrizes não cabem no cache L3, mais núcleos não trazem dados mais
  rápido. É o principal limite neste problema.
- **Overhead de comunicação** (MPI): Scatterv, Bcast e Gatherv crescem com p.
- **Overhead de criação e sincronização de threads** (OpenMP), relevante para N pequeno.
- **Núcleos lógicos (hyperthreading)** dividem as mesmas unidades de ponto flutuante:
  passar do número de núcleos físicos quase não ajuda.
