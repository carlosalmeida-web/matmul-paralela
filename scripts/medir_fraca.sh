#!/usr/bin/env bash
# ESCALABILIDADE FRACA: o tamanho do problema cresce junto com p, para que o
# trabalho POR thread/processo fique constante.
#
# O custo do produto e ~N^3. Para que N^3 / p fique constante:
#     N(p) = N0 * p^(1/3)
# Ex.: N0=512 -> p=1: 512, p=2: 645, p=4: 813, p=8: 1024
#
# Leitura do resultado: no caso ideal o TEMPO fica constante quando p cresce.
# Eficiencia fraca = T(p=1, N0) / T(p, N(p)); se cai, ha overhead que cresce
# com p (comunicacao no MPI, disputa por banda de memoria nos dois).
#
# Uso:  bash scripts/medir_fraca.sh
#       N0=768 bash scripts/medir_fraca.sh
#
# Gera: results/fraca.csv
source "$(dirname "$0")/comum.sh"
make -s all

N0=${N0:-512}
W=results/fraca.csv
echo "versao,N,p,rep,tempo,tempo_calculo,tempo_comunicacao,checksum,valido" > $W
for p in $PS; do
    N=$(python3 -c "print(round($N0 * $p ** (1/3)))")
    garante_ref "$N"
    echo "p=$p -> N=$N"
    for v in omp mpi; do
        for r in $(seq 0 $((REPS - 1))); do
            IFS=, read -r t c m chk <<< "$(roda $v "$N" "$p")"
            echo "$v,$N,$p,$r,$t,$c,$m,$chk,$(valida "$chk" "$N")" >> $W
        done
    done
done

if grep -q ",NAO$" $W; then echo "ATENCAO: ha resultados diferentes do baseline em $W"; exit 1; fi
echo "Pronto: $W"
