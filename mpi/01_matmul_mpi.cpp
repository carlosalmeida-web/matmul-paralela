/* Versao MPI 01 — Multiplicacao de matrizes densas C = A x B
 * Programacao Paralela (CCO085) — IESB 2026/2
 *
 * Paralelizacao do baseline sequencial (01_matmul.cpp) em memoria DISTRIBUIDA.
 *
 * Estrategia (decomposicao por faixas de linhas):
 *   - Rank 0 gera A e B (entrada IDENTICA ao baseline).
 *   - MPI_Scatterv : cada processo recebe um bloco de linhas de A
 *                    (Scatterv, e nao Scatter, porque N pode nao ser
 *                    divisivel pelo numero de processos).
 *   - MPI_Bcast    : B inteira e enviada para todos (todo processo precisa
 *                    de B completa para calcular suas linhas de C).
 *   - Cada processo calcula suas linhas de C com o mesmo laco i-k-j.
 *   - MPI_Gatherv  : rank 0 junta as faixas de C.
 *   - MPI_Reduce   : tempo final = maximo entre os processos (o mais lento).
 *   - Checksum sequencial no rank 0, mesma ordem do baseline
 *     => resultado identico bit a bit.
 *
 * Compilar: mpicxx -O2 -o 01_matmul_mpi 01_matmul_mpi.cpp
 * Executar: mpirun -np 4 ./01_matmul_mpi 512
 */
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <mpi.h>
using namespace std;

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank, P;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &P);

    int N = (argc > 1) ? atoi(argv[1]) : 512;

    // ---- decomposicao: quantas linhas cada processo recebe ----
    // N = base*P + resto: os 'resto' primeiros processos ficam com 1 linha a mais
    int base = N / P, resto = N % P;
    vector<int> linhas(P), inicio(P);       // linhas e 1a linha de cada rank
    vector<int> cntA(P), dspA(P);           // contagens/deslocamentos em elementos
    for (int r = 0; r < P; r++) {
        linhas[r] = base + (r < resto ? 1 : 0);
        inicio[r] = (r == 0) ? 0 : inicio[r-1] + linhas[r-1];
        cntA[r]   = linhas[r] * N;
        dspA[r]   = inicio[r] * N;
    }
    int minhas = linhas[rank];

    // ---- memoria: so o rank 0 guarda A e C completas ----
    vector<double> A, C, B(N*N), Aloc(minhas*N), Cloc(minhas*N, 0.0);
    if (rank == 0) {
        A.resize(N*N);
        C.resize(N*N);
        // entrada deterministica — IDENTICA ao baseline
        for (int i = 0; i < N*N; i++) { A[i] = (i % 100) * 0.01; B[i] = ((i * 7) % 100) * 0.01; }
    }

    MPI_Barrier(MPI_COMM_WORLD);            // todos comecam juntos
    double t0 = MPI_Wtime();

    // ---- comunicacao de entrada (operacoes coletivas) ----
    MPI_Scatterv(A.data(), cntA.data(), dspA.data(), MPI_DOUBLE,
                 Aloc.data(), minhas*N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Bcast(B.data(), N*N, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    // ---- computacao local: mesmo laco i-k-j, so que nas MINHAS linhas ----
    double tc0 = MPI_Wtime();
    const double* __restrict pA = Aloc.data();
    const double* __restrict pB = B.data();
    double* __restrict pC = Cloc.data();
    for (int i = 0; i < minhas; i++)
        for (int k = 0; k < N; k++) {
            double a = pA[i*N + k];
            for (int j = 0; j < N; j++)
                pC[i*N + j] += a * pB[k*N + j];
        }
    double tc1 = MPI_Wtime();

    // ---- comunicacao de saida ----
    MPI_Gatherv(Cloc.data(), minhas*N, MPI_DOUBLE,
                C.data(), cntA.data(), dspA.data(), MPI_DOUBLE, 0, MPI_COMM_WORLD);

    double t1 = MPI_Wtime();

    // ---- tempos: o que vale e o do processo mais lento ----
    double total_loc = t1 - t0, calc_loc = tc1 - tc0, total, calc;
    MPI_Reduce(&total_loc, &total, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&calc_loc,  &calc,  1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        // checksum sequencial (mesma ordem do baseline)
        double soma = 0.0;
        for (int i = 0; i < N*N; i++) soma += C[i];
        printf("N=%d  procs=%d  checksum=%.6f  tempo=%.6f s  (calculo=%.6f s, comunicacao=%.6f s)\n",
               N, P, soma, total, calc, total - calc);
        fprintf(stderr, "checksum_exato=%.17g\n", soma);
    }

    MPI_Finalize();
    return 0;
}
