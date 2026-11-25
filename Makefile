# Projeto 01 — Multiplicacao de matrizes densas (CCO085 — IESB 2026/2)
#
#   make            compila as tres versoes (sequencial, OpenMP, MPI)
#   make medir      roda a medicao completa e grava os CSVs em results/
#   make graficos   gera os graficos e o resumo a partir dos CSVs
#   make teste      confere rapidamente se OpenMP e MPI batem com o baseline
#   make clean      apaga os binarios
#
# Flags iguais as do enunciado (-O2) para que a comparacao seja justa:
# o baseline e as versoes paralelas sao compiladas com o mesmo nivel de otimizacao.

CXX      ?= g++
MPICXX   ?= mpicxx
CXXFLAGS ?= -O2 -Wall

SEQ   = sequential/01_matmul
PROF  = sequential/01_matmul_profile
OMP   = openmp/01_matmul_omp
MPI   = mpi/01_matmul_mpi

.PHONY: all seq omp mpi medir graficos teste clean

all: seq omp mpi

seq: $(SEQ) $(PROF)
omp: $(OMP)
mpi: $(MPI)

$(SEQ): sequential/01_matmul.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

$(PROF): sequential/01_matmul_profile.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

$(OMP): openmp/01_matmul_omp.cpp
	$(CXX) $(CXXFLAGS) -fopenmp -o $@ $<

$(MPI): mpi/01_matmul_mpi.cpp
	$(MPICXX) $(CXXFLAGS) -o $@ $<

medir: all
	bash scripts/medir.sh
	bash scripts/medir_escalonamento.sh
	bash scripts/medir_fraca.sh

graficos:
	python3 scripts/graficos.py

# Teste rapido de corretude: N=7 (pequeno e impar) e N=512, varios p.
teste: all
	@for N in 7 512; do \
	  ref=$$(./$(SEQ) $$N | sed 's/.*checksum=\([^ ]*\).*/\1/'); \
	  echo "N=$$N  baseline checksum=$$ref"; \
	  for p in 1 2 3 4; do \
	    o=$$(OMP_NUM_THREADS=$$p ./$(OMP) $$N 2>/dev/null | sed 's/.*checksum=\([^ ]*\).*/\1/'); \
	    m=$$(mpirun $(MPIRUN_FLAGS) --oversubscribe -np $$p ./$(MPI) $$N 2>/dev/null | sed 's/.*checksum=\([^ ]*\).*/\1/'); \
	    [ "$$o" = "$$ref" ] && so=OK || so=ERRO; [ "$$m" = "$$ref" ] && sm=OK || sm=ERRO; \
	    echo "   p=$$p  openmp=$$o [$$so]  mpi=$$m [$$sm]"; \
	  done; \
	done

clean:
	rm -f $(SEQ) $(PROF) $(OMP) $(MPI)
