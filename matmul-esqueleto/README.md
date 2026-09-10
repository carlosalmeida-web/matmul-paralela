# Projeto 01 — Multiplicação de Matrizes Densas

**Disciplina:** Programação Paralela (CCO085) — IESB, 2026/2
**Professor:** Rodrigo Gonçalves
**Trio:** Carlos E. Sousa, Guilherme Duarte, Yasmim Ferreira

Transformação do baseline sequencial `C = A x B` (fornecido pelo professor)
em versões paralelas com OpenMP (memória compartilhada) e MPI (memória
distribuída), mantendo o mesmo resultado (checksum) do código sequencial.

## Estrutura do repositório

```
.
├── sequential/   # baseline fornecido pelo professor + versão instrumentada de perfilamento
├── openmp/       # versão OpenMP (Etapa 2)
├── mpi/          # versão MPI (Etapa 3)
├── scripts/      # scripts de medição (gera CSV) e de plotagem (gera gráficos)
├── results/      # CSVs de medição e gráficos gerados
├── docs/         # documentos do projeto (relatórios em PDF)
├── Makefile
├── AUTORES.md
└── README.md
```

> Este README está em construção — cada responsável deve completar a seção
> referente à própria frente (como compilar, como rodar, como interpretar
> os resultados) conforme for implementando.

## Responsabilidades

| Frente | Responsável |
|---|---|
| Baseline e Perfilamento | Yasmim Ferreira |
| Versão OpenMP | Carlos Eduardo Souza |
| Versão MPI | Guilherme Duarte |

Detalhes em [AUTORES.md](AUTORES.md).

## Validação de corretude

Todas as versões (OpenMP e MPI) devem produzir o **mesmo checksum** do
baseline sequencial para o mesmo N. A entrada é determinística e a lógica de
cálculo não pode ser alterada — apenas paralelizada.
