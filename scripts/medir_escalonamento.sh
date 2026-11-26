#!/usr/bin/env bash
# Comparacao das politicas de escalonamento do OpenMP (static, dynamic, guided).
#
# Compila uma variante da versao OpenMP com -DSCHED_RUNTIME, em que o pragma usa
# schedule(runtime), e escolhe a politica pela variavel OMP_SCHEDULE.
# N fixo (padrao 1024) e p = numero maximo de threads da lista PS.
#
# Uso:  bash scripts/medir_escalonamento.sh
#       N_SCHED=1536 bash scripts/medir_escalonamento.sh
#
# Gera: results/escalonamento.csv
#
# Expectativa: como todas as linhas custam o mesmo (matriz densa, carga
# uniforme), static deve ser o melhor ou empatar; dynamic,1 deve ser o pior
# (uma linha por vez -> mais overhead de distribuicao e pior localidade).
source "$(dirname "$0")/comum.sh"
make -s all

N=${N_SCHED:-1024}
P=$(echo $PS | awk '{print $NF}')
BIN=./openmp/01_matmul_omp_sched
g++ -O2 -fopenmp -DSCHED_RUNTIME -o $BIN openmp/01_matmul_omp.cpp

garante_ref "$N"
E=results/escalonamento.csv
echo "politica,N,p,rep,tempo,checksum,valido" > $E
for pol in "static" "static,1" "dynamic,1" "dynamic,16" "guided"; do
    for r in $(seq 0 $((REPS - 1))); do
        out=$(OMP_SCHEDULE="$pol" OMP_NUM_THREADS=$P $BIN "$N" 2>/dev/null)
        t=$(echo "$out" | campo tempo); chk=$(echo "$out" | campo checksum)
        echo "\"$pol\",$N,$P,$r,$t,$chk,$(valida "$chk" "$N")" >> $E
    done
    echo "  $pol ok"
done
echo "Pronto: $E  (N=$N, $P threads)"
