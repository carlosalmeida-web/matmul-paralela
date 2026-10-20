/* Versao OpenMP 01 — Multiplicacao de matrizes densas C = A x B
 * Programacao Paralela (CCO085) — IESB 2026/2
 *
 * Paralelizacao do baseline sequencial (01_matmul.cpp) em memoria compartilhada.
 *
 * Compilar: g++ -O2 -fopenmp -o 01_matmul_omp 01_matmul_omp.cpp
 * Executar: OMP_NUM_THREADS=4 ./01_matmul_omp 512
 *
 * DECISOES DE PROJETO
 *
 * 1) Padrao escolhido: laco paralelo (parallel for) no laco externo i.
 *    Cada iteracao de i calcula UMA linha inteira de C. Linhas diferentes
 *    sao independentes, entao o trabalho divide-se sem comunicacao.
 *
 * 2) Condicoes de corrida: NAO existem no laco principal.
 *    - Cada thread escreve apenas nas linhas C[i][*] que lhe pertencem;
 *      nenhuma outra thread le ou escreve essas posicoes.
 *    - A e B sao apenas lidas (leitura concorrente e segura).
 *    - k, j e a sao declaradas dentro do laco -> privadas de cada thread.
 *    Por isso nao ha critical, atomic nem reduction no calculo: qualquer
 *    um deles so adicionaria sincronizacao desnecessaria.
 *    Contraexemplo: se paralelizassemos o laco k, varias threads somariam
 *    no mesmo C[i][j] ao mesmo tempo -> corrida. Seria preciso atomic
 *    (lentissimo, N^3 operacoes atomicas) ou reduction por elemento.
 *
 * 3) Resultado identico ao baseline (bit a bit):
 *    cada C[i][j] continua acumulando em k = 0, 1, ..., N-1, na mesma
 *    ordem do sequencial. Mudar quem calcula a linha nao muda a ordem
 *    das somas, logo nao muda o arredondamento.
 *
 * 4) Checksum mantido SEQUENCIAL de proposito.
 *    Um "reduction(+:soma)" mudaria a ordem das somas em ponto flutuante
 *    (que nao e associativo) e o checksum poderia divergir nas ultimas
 *    casas. E O(N^2), irrelevante perto do O(N^3) do produto.
 *
 * 5) Escalonamento: schedule(static).
 *    Todas as linhas custam exatamente o mesmo (N*N multiplicacoes),
 *    entao nao ha desbalanceamento: dynamic/guided so somariam overhead.
 *    O static entrega blocos contiguos de linhas a cada thread, o que
 *    tambem minimiza false sharing (fronteiras so entre blocos).
 *    Pode ser trocado em tempo de execucao com OMP_SCHEDULE, pois o
 *    pragma usa schedule(runtime) quando compilado com -DSCHED_RUNTIME.
 */
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <omp.h>
using namespace std;

int main(int argc, char** argv) {
    int N = (argc > 1) ? atoi(argv[1]) : 512;
    vector<double> A(N*N), B(N*N), C(N*N, 0.0);

    // entrada deterministica — IDENTICA ao baseline (nao pode ser alterada)
    for (int i = 0; i < N*N; i++) { A[i] = (i % 100) * 0.01; B[i] = ((i * 7) % 100) * 0.01; }

    int nthreads = 1;
    #pragma omp parallel
    {
        #pragma omp single
        nthreads = omp_get_num_threads();
    }

    // ponteiros crus com __restrict: garantem ao compilador que A, B e C nao
    // se sobrepoem, para que o laco j seja vetorizado dentro da regiao
    // paralela igual ao baseline (sem isso, 1 thread fica mais lento que o
    // sequencial). Nao muda a ordem das operacoes nem o resultado.
    const double* __restrict pA = A.data();
    const double* __restrict pB = B.data();
    double* __restrict pC = C.data();

    double t0 = omp_get_wtime();
#ifdef SCHED_RUNTIME
    #pragma omp parallel for schedule(runtime)
#else
    #pragma omp parallel for schedule(static)
#endif
    for (int i = 0; i < N; i++)
        for (int k = 0; k < N; k++) {
            double a = pA[i*N + k];
            for (int j = 0; j < N; j++)
                pC[i*N + j] += a * pB[k*N + j];
        }
    double t1 = omp_get_wtime();

    // checksum sequencial (mesma ordem de soma do baseline)
    double soma = 0.0;
    for (int i = 0; i < N*N; i++) soma += C[i];
    printf("N=%d  threads=%d  checksum=%.6f  tempo=%.6f s\n", N, nthreads, soma, t1 - t0);
    // checksum com todas as casas, para comparacao exata com o baseline
    fprintf(stderr, "checksum_exato=%.17g\n", soma);
    return 0;
}
