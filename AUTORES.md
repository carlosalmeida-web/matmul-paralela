# Autores e Responsabilidades

Projeto 01 — Multiplicação de Matrizes Densas
Programação Paralela (CCO085) — IESB, 2026/2 — Prof. Rodrigo Gonçalves

| Nome | Frente / Responsabilidade | Entregável principal |
|---|---|---|
| Yasmim Ferreira | Etapa 1 — Baseline e Perfilamento | Análise do algoritmo sequencial, perfilamento (hotspots), protocolo de medição, fração paralelizável e Lei de Amdahl |
| Carlos Eduardo Souza | Etapa 2 — Versão OpenMP (memória compartilhada) | Implementação OpenMP a partir do baseline, tratamento de condições de corrida, comparação de políticas de escalonamento, curva de speedup por número de threads |
| Guilherme Duarte | Etapa 3 — Versão MPI (memória distribuída) | Implementação MPI a partir do baseline, decomposição de dados, uso de operação coletiva, análise de overhead de comunicação, curva de speedup por número de processos |