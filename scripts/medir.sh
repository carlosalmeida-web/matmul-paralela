#!/usr/bin/env bash
# Medicao principal: baseline, perfilamento e ESCALABILIDADE FORTE
# (N fixo, aumentando threads/processos) das tres versoes.
#
# Uso:   make medir            (roda este e os outros dois scripts)
#   ou:  bash scripts/medir.sh
#        NS="512 1024" PS="1 2 4" REPS=4 bash scripts/medir.sh
#
# Gera:
#   results/perfil.csv   tempo de cada trecho do programa sequencial (hotspots)
#   results/forte.csv    tempo das tres versoes para cada N e p
#   results/maquina.txt  descricao da maquina e dos parametros usados
#
# Protocolo (repeticoes, aquecimento, mediana): ver scripts/comum.sh
source "$(dirname "$0")/comum.sh"
make -s all
registra_maquina
echo "Maquina: $NUCLEOS nucleos logicos | NS='$NS' | PS='$PS' | REPS=$REPS"

# ---- 1) perfilamento do sequencial ----
echo "rep,N,alocacao,inicializacao,multiplicacao,checksum_tempo,total,checksum" > results/perfil.csv
for N in $NS; do
    for r in $(seq 0 $((REPS - 1))); do
        echo "$r,$($PROF "$N")" >> results/perfil.csv
    done
    echo "perfil N=$N ok"
done

# ---- 2) escalabilidade forte ----
F=results/forte.csv
echo "versao,N,p,rep,tempo,tempo_calculo,tempo_comunicacao,checksum,valido" > $F
for N in $NS; do
    garante_ref "$N"
    echo "N=$N  checksum de referencia: ${REF[$N]}"
    for r in $(seq 0 $((REPS - 1))); do
        IFS=, read -r t c m chk <<< "$(roda seq "$N" 1)"
        echo "seq,$N,1,$r,$t,$c,$m,$chk,sim" >> $F
    done
    for v in omp mpi; do
        for p in $PS; do
            for r in $(seq 0 $((REPS - 1))); do
                IFS=, read -r t c m chk <<< "$(roda $v "$N" "$p")"
                echo "$v,$N,$p,$r,$t,$c,$m,$chk,$(valida "$chk" "$N")" >> $F
            done
            echo "  $v p=$p ok"
        done
    done
done

if grep -q ",NAO$" $F; then echo "ATENCAO: ha resultados diferentes do baseline em $F"; exit 1; fi
echo "Pronto: results/perfil.csv e $F (todos os checksums conferem com o baseline)"
