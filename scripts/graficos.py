#!/usr/bin/env python3
"""Gera os graficos e o resumo da analise experimental a partir dos CSVs.

Uso:  make graficos     (ou: python3 scripts/graficos.py)

Entrada (geradas pelos scripts medir*.sh):
  results/perfil.csv, results/forte.csv,
  results/escalonamento.csv (opcional), results/fraca.csv (opcional)

Saida em results/:
  tempo.png, speedup.png, eficiencia.png, amdahl.png, mpi_comunicacao.png,
  escalonamento.png, fraca.png e resumo.md (todas as tabelas com os numeros)

Definicoes usadas
  - Descarta a execucao rep=0 (aquecimento) e usa a MEDIANA das demais.
  - Speedup     S(p) = T_seq / T_par(p)  (T_seq = baseline sequencial, mesmo N)
  - Eficiencia  E(p) = S(p) / p          (1,0 = aproveitamento perfeito)
  - Os programas cronometram SO a multiplicacao (+ comunicacao, no MPI).
    Por isso ha dois speedups:
      * speedup do nucleo  = T_mult_seq / T_par(p)   (graficos speedup/eficiencia)
      * speedup do programa = T_total_seq / (T_serial + T_par(p)), em que
        T_serial = alocacao + inicializacao + checksum (do perfilamento),
        partes que continuam sequenciais. E ESTE que se compara com Amdahl.
  - Amdahl      S(p) = 1 / ((1-f) + f/p), com f = fracao do tempo do baseline
                gasta na multiplicacao (medida no perfilamento).
  - Escalabilidade fraca: eficiencia = T(p=1, N0) / T(p, N(p)).
"""
import csv
import os
import statistics
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
# paleta categorica validada (daltonismo e contraste); cada serie tem tambem
# um marcador proprio, para nao depender so da cor
CORES = ["#257de0", "#f47230", "#00b894", "#f2a600"]
MARCAS = ["o", "s", "^", "D"]
CINZA, TEXTO, TEXTO2 = "#9c9c9c", "#191919", "#666666"
NOMES = {"seq": "Sequencial", "omp": "OpenMP", "mpi": "MPI"}

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": "#cccccc", "axes.labelcolor": TEXTO,
    "xtick.color": TEXTO2, "ytick.color": TEXTO2, "axes.grid": True,
    "grid.color": "#eeeeee", "grid.linewidth": 0.8, "axes.spines.top": False,
    "axes.spines.right": False, "legend.frameon": False, "lines.linewidth": 2,
    "lines.markersize": 7, "axes.axisbelow": True, "figure.dpi": 150, "savefig.bbox": "tight",
})


def le_csv(nome):
    caminho = os.path.join(RES, nome)
    if not os.path.exists(caminho):
        return None
    with open(caminho, newline="") as f:
        return [r for r in csv.DictReader(f) if r["rep"] != "0"]  # descarta aquecimento


def med(valores):
    return statistics.median(valores)


def fmt(x, casas=3):
    return f"{x:.{casas}f}".replace(".", ",")


def amdahl(f, p):
    return 1.0 / ((1 - f) + f / p)


md = ["# Resumo da análise experimental", "",
      "_Gerado automaticamente por `scripts/graficos.py` a partir dos CSVs em `results/`. "
      "Mediana das repetições, descartando a 1ª (aquecimento)._", ""]
if os.path.exists(os.path.join(RES, "maquina.txt")):
    md += ["## Máquina", "", "```", open(os.path.join(RES, "maquina.txt")).read().strip(), "```", ""]

# ---------------------------------------------------------------- perfilamento
perfil = le_csv("perfil.csv")
f_por_N, serial_por_N, total_por_N, mult_por_N = {}, {}, {}, {}
if perfil:
    md += ["## 1. Perfilamento do baseline (hotspots)", "",
           "| N | Alocação | Inicialização | **Multiplicação** | Checksum | Total | f | Amdahl S_max |",
           "|---|---|---|---|---|---|---|---|"]
    por_N = defaultdict(list)
    for r in perfil:
        por_N[int(r["N"])].append(r)
    for N in sorted(por_N):
        rs = por_N[N]
        m = {k: med([float(r[k]) for r in rs])
             for k in ("alocacao", "inicializacao", "multiplicacao", "checksum_tempo", "total")}
        f = m["multiplicacao"] / m["total"]
        f_por_N[N] = f
        serial_por_N[N] = m["total"] - m["multiplicacao"]
        total_por_N[N] = m["total"]
        mult_por_N[N] = m["multiplicacao"]
        cel = lambda k: f"{fmt(m[k]*1000, 2)} ms ({fmt(100*m[k]/m['total'], 1)}%)"
        md.append(f"| {N} | {cel('alocacao')} | {cel('inicializacao')} | **{cel('multiplicacao')}** | "
                  f"{cel('checksum_tempo')} | {fmt(m['total'], 4)} s | {fmt(f, 4)} | {fmt(1/(1-f), 1)} |")
    md += ["", "f = fração do tempo na multiplicação (a parte paralelizada). "
           "S_max = 1/(1−f) é o speedup máximo com infinitos núcleos.", ""]

# ---------------------------------------------------------- escalabilidade forte
forte = le_csv("forte.csv")
if not forte:
    raise SystemExit("results/forte.csv nao encontrado: rode antes  make medir")

T = defaultdict(list)       # (versao, N, p) -> tempos
COMM = defaultdict(list)    # (N, p) -> tempos de comunicacao do MPI
for r in forte:
    chave = (r["versao"], int(r["N"]), int(r["p"]))
    T[chave].append(float(r["tempo"]))
    if r["versao"] == "mpi":
        COMM[(int(r["N"]), int(r["p"]))].append(float(r["tempo_comunicacao"]))
T = {k: med(v) for k, v in T.items()}
Ns = sorted({k[1] for k in T})
Ps = sorted({k[2] for k in T if k[0] != "seq"})
invalidos = sum(1 for r in forte if r["valido"] != "sim")

md += ["## 2. Validação de corretude", "",
       f"{len(forte)} execuções paralelas e sequenciais conferidas contra o checksum do baseline: "
       + ("**todas idênticas**." if invalidos == 0 else f"**{invalidos} DIFERENTES — investigar!**"), "",
       "| N | checksum do baseline |", "|---|---|"]
for N in Ns:
    chk = next(r["checksum"] for r in forte if r["versao"] == "seq" and int(r["N"]) == N)
    md.append(f"| {N} | {chk} |")
md.append("")

def speedup_programa(v, N, p):
    # o baseline usa o tempo medido no perfilamento para manter as duas medidas coerentes
    t_par = T[(v, N, p)] * (mult_por_N[N] / T[("seq", N, 1)])
    return total_por_N[N] / (serial_por_N[N] + t_par)


md += ["## 3. Escalabilidade forte (N fixo)", ""]
for v in ("omp", "mpi"):
    md += [f"### {NOMES[v]}", "",
           "| N | p | Tempo (s) | Speedup do núcleo | Eficiência | Speedup do programa | Amdahl previsto |",
           "|---|---|---|---|---|---|---|"]
    for N in Ns:
        ts = T[("seq", N, 1)]
        md.append(f"| {N} | seq | {fmt(ts, 4)} | 1,00 | — | 1,00 | — |")
        for p in Ps:
            if (v, N, p) not in T:
                continue
            s = ts / T[(v, N, p)]
            am = fmt(amdahl(f_por_N[N], p), 2) if N in f_por_N else "—"
            sp = fmt(speedup_programa(v, N, p), 2) if N in f_por_N else "—"
            md.append(f"| {N} | {p} | {fmt(T[(v, N, p)], 4)} | {fmt(s, 2)} | {fmt(s/p, 2)} | {sp} | {am} |")
    md.append("")
md += ["**Speedup do núcleo**: só a multiplicação (o trecho cronometrado). "
       "**Speedup do programa**: estimado somando as partes que continuam sequenciais "
       "(alocação, inicialização, checksum, medidas no perfilamento); é este que se compara com Amdahl. "
       "Speedup do programa abaixo do previsto indica overhead que Amdahl não modela "
       "(comunicação, banda de memória, sincronização).", ""]


def eixo_p(ax):
    ax.set_xscale("log", base=2)
    ax.set_xticks(Ps)
    ax.set_xticklabels([str(p) for p in Ps])
    ax.minorticks_off()


def painel(nome_arq, titulo, ylabel, valor, ideal=None, logy=False):
    fig, axs = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, v in zip(axs, ("omp", "mpi")):
        if ideal == "linear":
            ax.plot(Ps, Ps, "--", color=CINZA, linewidth=1.2, label="ideal")
        elif ideal == "um":
            ax.axhline(1.0, linestyle="--", color=CINZA, linewidth=1.2, label="ideal")
        for i, N in enumerate(Ns):
            pts = [(p, valor(v, N, p)) for p in Ps if (v, N, p) in T]
            ax.plot([a for a, _ in pts], [b for _, b in pts], marker=MARCAS[i % 4],
                    color=CORES[i % 4], label=f"N = {N}")
        eixo_p(ax)
        if logy:
            ax.set_yscale("log")
        ax.set_title(NOMES[v], color=TEXTO, loc="left", fontsize=11)
        ax.set_xlabel("threads" if v == "omp" else "processos")
    axs[0].set_ylabel(ylabel)
    axs[1].legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=9)
    fig.suptitle(titulo, x=0.02, y=1.04, ha="left", color=TEXTO, fontsize=12)
    fig.savefig(os.path.join(RES, nome_arq))
    plt.close(fig)


painel("tempo.png", "Tempo de execução da multiplicação (escala log)", "tempo (s)",
       lambda v, N, p: T[(v, N, p)], logy=True)
painel("speedup.png", "Speedup da multiplicação em relação ao baseline sequencial", "speedup",
       lambda v, N, p: T[("seq", N, 1)] / T[(v, N, p)], ideal="linear")

# Amdahl: speedup do PROGRAMA (estimado) x previsao, para o maior N
if f_por_N:
    N = max(n for n in Ns if n in f_por_N)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(Ps, Ps, "--", color=CINZA, linewidth=1.2, label="ideal (linear)")
    ax.plot(Ps, [amdahl(f_por_N[N], p) for p in Ps], ":", color=TEXTO2, linewidth=2,
            label=f"Amdahl (f = {fmt(f_por_N[N], 3)})")
    for i, v in enumerate(("omp", "mpi")):
        ps = [p for p in Ps if (v, N, p) in T]
        ax.plot(ps, [speedup_programa(v, N, p) for p in ps], marker=MARCAS[i], color=CORES[i],
                label=f"{NOMES[v]} medido")
    eixo_p(ax)
    ax.set_xlabel("threads / processos"); ax.set_ylabel("speedup do programa inteiro")
    ax.set_title(f"Medido x Lei de Amdahl (N = {N})", loc="left", color=TEXTO, fontsize=12)
    ax.legend()
    fig.savefig(os.path.join(RES, "amdahl.png")); plt.close(fig)
painel("eficiencia.png", "Eficiência (speedup / p)", "eficiência",
       lambda v, N, p: T[("seq", N, 1)] / T[(v, N, p)] / p, ideal="um")

# ---------------------------------------------------------- overhead do MPI
md += ["## 4. Overhead de comunicação do MPI", "",
       "| N | p | Tempo total (s) | Comunicação (s) | % do tempo em comunicação |", "|---|---|---|---|---|"]
fig, ax = plt.subplots(figsize=(6, 4))
for i, N in enumerate(Ns):
    xs, ys = [], []
    for p in Ps:
        if (N, p) in COMM:
            c, tot = med(COMM[(N, p)]), T[("mpi", N, p)]
            xs.append(p); ys.append(100 * c / tot)
            md.append(f"| {N} | {p} | {fmt(tot, 4)} | {fmt(c, 4)} | {fmt(100*c/tot, 1)}% |")
    ax.plot(xs, ys, marker=MARCAS[i % 4], color=CORES[i % 4], label=f"N = {N}")
eixo_p(ax)
ax.set_xlabel("processos"); ax.set_ylabel("% do tempo em comunicação")
ax.set_ylim(bottom=0)
ax.set_title("MPI: fração do tempo gasta em comunicação", loc="left", color=TEXTO, fontsize=12)
ax.legend()
fig.savefig(os.path.join(RES, "mpi_comunicacao.png")); plt.close(fig)
md.append("")

# ---------------------------------------------------------- escalonamento
esc = le_csv("escalonamento.csv")
if esc:
    por = defaultdict(list)
    for r in esc:
        por[r["politica"]].append(float(r["tempo"]))
    ordem = list(dict.fromkeys(r["politica"] for r in esc))
    meds = [med(por[k]) for k in ordem]
    N, p = esc[0]["N"], esc[0]["p"]
    md += [f"## 5. Políticas de escalonamento do OpenMP (N = {N}, {p} threads)", "",
           "| Política | Tempo (s) | Relativo ao static |", "|---|---|---|"]
    for k, t in zip(ordem, meds):
        md.append(f"| `{k}` | {fmt(t, 4)} | {fmt(t/meds[0], 2)}× |")
    md.append("")
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.barh(ordem[::-1], meds[::-1], color=CORES[0], height=0.6, edgecolor="white", linewidth=2)
    for y, t in enumerate(meds[::-1]):
        ax.text(t, y, f" {fmt(t, 3)} s", va="center", color=TEXTO, fontsize=9)
    ax.set_xlabel("tempo (s) — menor é melhor"); ax.grid(axis="y", visible=False)
    ax.set_xlim(right=max(meds) * 1.18)
    ax.set_title(f"OpenMP: escalonamento (N = {N}, {p} threads)", loc="left", color=TEXTO, fontsize=12)
    fig.savefig(os.path.join(RES, "escalonamento.png")); plt.close(fig)

# ---------------------------------------------------------- escalabilidade fraca
fraca = le_csv("fraca.csv")
if fraca:
    W = defaultdict(list)
    for r in fraca:
        W[(r["versao"], int(r["p"]))].append((int(r["N"]), float(r["tempo"])))
    md += ["## 6. Escalabilidade fraca (trabalho por thread/processo constante)", "",
           "N(p) = N0 · p^(1/3), para que N³/p fique constante. Ideal: tempo constante, eficiência 1,0.", "",
           "| Versão | p | N | Tempo (s) | Eficiência fraca |", "|---|---|---|---|---|"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.axhline(1.0, linestyle="--", color=CINZA, linewidth=1.2, label="ideal")
    for i, v in enumerate(("omp", "mpi")):
        ps = sorted(p for (vv, p) in W if vv == v)
        if not ps:
            continue
        t1 = med([t for _, t in W[(v, ps[0])]])
        effs = []
        for p in ps:
            N = W[(v, p)][0][0]
            t = med([t for _, t in W[(v, p)]])
            effs.append(t1 / t)
            md.append(f"| {NOMES[v]} | {p} | {N} | {fmt(t, 4)} | {fmt(t1/t, 2)} |")
        ax.plot(ps, effs, marker=MARCAS[i], color=CORES[i], label=NOMES[v])
    eixo_p(ax)
    ax.set_ylim(0, 1.15)
    ax.set_xlabel("threads / processos"); ax.set_ylabel("eficiência fraca")
    ax.set_title("Escalabilidade fraca", loc="left", color=TEXTO, fontsize=12)
    ax.legend()
    fig.savefig(os.path.join(RES, "fraca.png")); plt.close(fig)
    md.append("")

with open(os.path.join(RES, "resumo.md"), "w") as f:
    f.write("\n".join(md) + "\n")
print("Graficos e resumo gerados em results/:",
      ", ".join(sorted(x for x in os.listdir(RES) if x.endswith((".png", ".md")))))
