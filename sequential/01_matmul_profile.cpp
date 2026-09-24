/* Baseline 01 — Multiplicacao de matrizes densas C = A x B
 * Programacao Paralela (CCO085) — IESB 2026/2 — Prof. Rodrigo Goncalves Pinto
 *
 * Ponto de partida sequencial. O trio deve paralelizar em OpenMP e MPI.
 * Aspecto interessante: efeito de cache e ordem de lacos.
 *
 * Compilar: g++ -O2 -o 01_matmul 01_matmul.cpp
 * Executar: ./01_matmul 512        (matriz N x N; padrao 512)
 */
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <ctime>
using namespace std;

static double agora() {
    timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

int main(int argc, char** argv) {
    int N = (argc > 1) ? atoi(argv[1]) : 512;

    double t_total0 = agora();

    // Alocação
    double t0 = agora();
    vector<double> A(N*N), B(N*N), C(N*N, 0.0);
    double t1 = agora();

    // Inicialização
    double t2 = agora();
    for (int i = 0; i < N*N; i++) {
        A[i] = (i % 100) * 0.01;
        B[i] = ((i * 7) % 100) * 0.01;
    }
    double t3 = agora();

    // Multiplicação
    double t4 = agora();
    for (int i = 0; i < N; i++)
        for (int k = 0; k < N; k++) {
            double a = A[i*N + k];

            for (int j = 0; j < N; j++)
                C[i*N + j] += a * B[k*N + j];
        }
    double t5 = agora();

    // Checksum
    double t6 = agora();
    double soma = 0.0;

    for (int i = 0; i < N*N; i++)
        soma += C[i];

    double t7 = agora();

    double t_total1 = agora();

    printf("N=%d\n", N);
    printf("checksum=%.6f\n", soma);
    printf("alocacao=%.6f s\n", t1 - t0);
    printf("inicializacao=%.6f s\n", t3 - t2);
    printf("multiplicacao=%.6f s\n", t5 - t4);
    printf("checksum_tempo=%.6f s\n", t7 - t6);
    printf("total=%.6f s\n", t_total1 - t_total0);

    return 0;
}