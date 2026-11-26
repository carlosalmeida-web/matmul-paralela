/* Perfilamento 01 — copia INSTRUMENTADA do baseline (01_matmul.cpp)
 * Programacao Paralela (CCO085) — IESB 2026/2
 *
 * A logica de calculo e a entrada sao IDENTICAS ao baseline fornecido;
 * so foram acrescentados cronometros em volta de cada trecho, para medir
 * onde o programa gasta o tempo (hotspots).
 *
 * Compilar: make seq     (ou: g++ -O2 -o 01_matmul_profile 01_matmul_profile.cpp)
 * Executar: ./01_matmul_profile 512
 * Saida:    uma linha CSV, para ser coletada por scripts/medir.sh:
 *           N,alocacao,inicializacao,multiplicacao,checksum_tempo,total,checksum
 *           (tempos em segundos)
 *
 * POR QUE CRONOMETROS MANUAIS E NAO gprof?
 *   O gprof mede tempo POR FUNCAO. Aqui todo o trabalho esta dentro do main,
 *   entao ele so diria "100% no main". Cronometros por trecho mostram que o
 *   hotspot e o laco triplo da multiplicacao.
 *
 * COMPLEXIDADE DE CADA TRECHO
 *   alocacao       O(N^2)  (os vector zeram a memoria)
 *   inicializacao  O(N^2)
 *   multiplicacao  O(N^3)  <- hotspot; o unico trecho que paralelizamos
 *   checksum       O(N^2)  (mantido sequencial nas versoes paralelas)
 *   Como N^3 cresce mais rapido que N^2, a fracao paralelizavel f
 *   AUMENTA com N, e com ela o speedup maximo de Amdahl, 1/(1-f).
 *
 * CLOCK_MONOTONIC: relogio que nao volta para tras nem salta se o horario do
 * sistema for ajustado — o adequado para medir intervalos.
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

    // Alocacao
    double t0 = agora();
    vector<double> A(N*N), B(N*N), C(N*N, 0.0);
    double t1 = agora();

    // Inicializacao (entrada deterministica, igual ao baseline)
    for (int i = 0; i < N*N; i++) {
        A[i] = (i % 100) * 0.01;
        B[i] = ((i * 7) % 100) * 0.01;
    }
    double t2 = agora();

    // Multiplicacao (mesmo laco i-k-j do baseline)
    for (int i = 0; i < N; i++)
        for (int k = 0; k < N; k++) {
            double a = A[i*N + k];
            for (int j = 0; j < N; j++)
                C[i*N + j] += a * B[k*N + j];
        }
    double t3 = agora();

    // Checksum
    double soma = 0.0;
    for (int i = 0; i < N*N; i++)
        soma += C[i];
    double t4 = agora();

    printf("%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\n",
           N, t1 - t0, t2 - t1, t3 - t2, t4 - t3, t4 - t0, soma);
    return 0;
}
