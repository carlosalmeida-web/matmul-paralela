# Etapa 3 — Versão MPI (memória distribuída)

**Responsável:** Guilherme Duarte

Código: `mpi/01_matmul_mpi.cpp` (as justificativas também estão no cabeçalho do arquivo).

## Decomposição

**Decomposição de domínio por faixas de linhas (1D).** Cada processo (rank) recebe um
bloco contíguo de linhas de A e calcula as linhas correspondentes de C. É a mesma
ideia do OpenMP, mas cada processo tem a **sua própria memória**; os dados só
trafegam por mensagens.

Divisão: `N = base·P + resto`; os `resto` primeiros ranks recebem uma linha a mais.
Ex.: N = 1000, P = 3 → 334, 333 e 333 linhas. A diferença máxima é de 1 linha,
então a carga fica equilibrada.

## Operações coletivas

| Operação | Para quê | Por que essa |
|---|---|---|
| `MPI_Scatterv` | distribuir as faixas de linhas de A | o "v" permite faixas de tamanhos diferentes (N não divisível por P) |
| `MPI_Bcast` | enviar B inteira a todos | para calcular qualquer linha de C é preciso B completa |
| `MPI_Gatherv` | juntar as faixas de C no rank 0 | mesmo motivo do Scatterv |
| `MPI_Reduce` (`MPI_MAX`) | tempo final | o programa só termina quando o processo mais lento termina |

O checksum é calculado no rank 0, sequencialmente e na mesma ordem do baseline →
resultado idêntico bit a bit, para qualquer número de processos.

## Overhead de comunicação

Volume de dados (em doubles):

- Scatterv de A: N² no total
- Bcast de B: (P − 1)·N² → **cresce com P**
- Gatherv de C: N² no total

Cálculo por processo: N³/P → **cai com P**.

Logo, a fração do tempo em comunicação **aumenta com P** e diminui com N (N³ cresce
mais rápido que N²). Medido em `results/mpi_comunicacao.png` e
`results/resumo.md` (seção 4): o programa separa o tempo de **cálculo** do de
**comunicação**.

Limitações desta decomposição:

- cada processo guarda B inteira (N² doubles): a memória por processo não cai com P;
- uma decomposição 2D (Cannon, SUMMA) trocaria só blocos de B e escalaria melhor,
  com código bem mais complexo.

Numa única máquina o OpenMPI troca mensagens por memória compartilhada, bem mais
rápido que pela rede; num cluster o overhead seria maior.

## Medição

- `MPI_Barrier` antes de iniciar o cronômetro: todos começam juntos.
- O tempo **inclui** a comunicação: é o custo real de usar MPI.
- A geração de A e B fica fora do cronômetro, como no baseline.

## Escalabilidade forte × fraca

- **Forte** (`results/speedup.png`): N fixo, aumentando P. Mede quanto mais rápido
  um problema fixo fica.
- **Fraca** (`results/fraca.png`, `scripts/medir_fraca.sh`): N cresce com P para que
  o trabalho por processo fique constante. Como o custo é N³,
  `N(P) = N0 · P^(1/3)` (ex.: 512, 645, 813, 1024 para P = 1, 2, 4, 8).
  No ideal o tempo fica constante (eficiência fraca = 1,0). Ela cai porque o Bcast
  de B cresce com P **e** com N, e porque os processos disputam a mesma banda de
  memória.
