# Funcoes e parametros compartilhados pelos scripts de medicao.
# Nao e executado sozinho: os scripts medir*.sh fazem "source" deste arquivo.
#
# PROTOCOLO DE MEDICAO (vale para todos os scripts)
#   - REPS execucoes por configuracao (padrao 6).
#   - A execucao rep=0 e AQUECIMENTO: fica gravada no CSV, mas e descartada
#     na analise (caches e paginas de memoria ainda "frios").
#   - Na analise (scripts/graficos.py) usamos a MEDIANA das demais: uma
#     execucao atrapalhada pelo sistema operacional distorce a media, mas
#     quase nao mexe na mediana.
#   - Toda execucao paralela tem o checksum comparado com o do baseline para
#     o mesmo N (coluna "valido").
#
# Parametros (podem ser trocados na linha de comando, ex.: REPS=3 bash scripts/medir.sh)
#   NS            tamanhos de matriz          (padrao "512 1024 1536")
#   PS            threads / processos         (padrao 1 2 4 8 ... ate o n. de nucleos)
#   REPS          repeticoes por configuracao (padrao 6)
#   MPIRUN_FLAGS  flags extras do mpirun      (padrao "--oversubscribe";
#                 em conteiner Docker como root, acrescente --allow-run-as-root)

set -euo pipefail
cd "$(dirname "$0")/.."

NUCLEOS=$(nproc)
if [ -z "${PS:-}" ]; then
    PS=""; p=1
    while [ "$p" -le "$NUCLEOS" ]; do PS="$PS $p"; p=$((p * 2)); done
    # inclui o total de nucleos se nao for potencia de 2 (ex.: 6, 12)
    case " $PS " in *" $NUCLEOS "*) ;; *) PS="$PS $NUCLEOS";; esac
fi
NS=${NS:-"512 1024 1536"}
REPS=${REPS:-6}
MPIRUN_FLAGS=${MPIRUN_FLAGS:-"--oversubscribe"}

SEQ=./sequential/01_matmul
PROF=./sequential/01_matmul_profile
OMP=./openmp/01_matmul_omp
MPI=./mpi/01_matmul_mpi

mkdir -p results

# extrai "campo=valor" da saida dos programas
campo() { sed -n "s/.*[ (]$1=\([^ )]*\).*/\1/p; s/^$1=\([^ )]*\).*/\1/p" | head -1; }

# checksum de referencia do baseline para um N (guardado em cache).
# garante_ref precisa ser chamada no shell principal (fora de $(...)),
# senao o cache se perde e o baseline seria rodado a cada validacao.
declare -A REF
garante_ref() {
    local N=$1
    if [ -z "${REF[$N]:-}" ]; then REF[$N]=$($SEQ "$N" | campo checksum); fi
}
ref_checksum() { garante_ref "$1"; echo "${REF[$1]}"; }

valida() {  # valida <checksum_obtido> <N>
    if [ "$1" = "$(ref_checksum "$2")" ]; then echo sim
    else echo "NAO"; echo "  !! checksum diferente do baseline: N=$2 obtido=$1 esperado=$(ref_checksum "$2")" >&2
    fi
}

# roda uma versao e imprime: tempo,tempo_calculo,tempo_comunicacao,checksum
roda() {  # roda <seq|omp|mpi> <N> <p>
    local v=$1 N=$2 p=$3 out
    case $v in
        seq) out=$($SEQ "$N") ;;
        omp) out=$(OMP_NUM_THREADS=$p $OMP "$N" 2>/dev/null) ;;
        mpi) out=$(mpirun $MPIRUN_FLAGS -np "$p" $MPI "$N" 2>/dev/null) ;;
    esac
    local t calc comm chk
    t=$(echo "$out" | campo tempo)
    chk=$(echo "$out" | campo checksum)
    calc=$(echo "$out" | campo calculo); comm=$(echo "$out" | campo comunicacao)
    [ -z "$calc" ] && calc=$t
    [ -z "$comm" ] && comm=0
    echo "$t,$calc,$comm,$chk"
}

registra_maquina() {
    {
        echo "data: $(date '+%Y-%m-%d %H:%M')"
        echo "host: $(hostname)"
        echo "nucleos logicos (nproc): $NUCLEOS"
        lscpu 2>/dev/null | grep -E "Model name|^Socket|Core\(s\) per socket|Thread\(s\) per core|L1d|L2|L3" || true
        echo "compilador: $(g++ --version | head -1)"
        echo "mpi: $(mpirun --version 2>/dev/null | head -1)"
        echo "parametros: NS='$NS' PS='$PS' REPS=$REPS"
    } > results/maquina.txt
}
