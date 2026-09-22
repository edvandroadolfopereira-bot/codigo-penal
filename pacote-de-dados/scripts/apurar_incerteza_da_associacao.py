# -*- coding: utf-8 -*-
"""Incerteza da associacao entre a serie de violencia e a de agravamento (Tabela 11), 22/09/2026.

A Tabela 11 trazia so' os coeficientes, sem intervalo nem p, e a auditoria de 16/09/2026
apontou isso (item 3.8). Este script refaz os seis coeficientes a partir da serie gravada em
analise-cientifica/cruzamento-violencia-e-severidade.json e acrescenta:
  - intervalo de confianca de 95% do coeficiente de Pearson, pela transformacao de Fisher,
    que e' aproximada com n de 12 a 14;
  - p bilateral por permutacao, o mesmo metodo dos demais testes do trabalho, com 200.000
    sorteios e semente fixa, para Pearson e para Spearman.

As tres especificacoes sao as da Tabela 11: nivel (n = 14); primeira diferenca das duas
series (n = 13); primeira diferenca com a de agravamento defasada um ano (n = 12).

Grava analise-cientifica/incerteza-da-associacao.json. --bancada roda os testes do calculo.
"""
import io
import json
import math
import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
R = os.path.dirname(os.path.abspath(__file__))
ENTRADA = os.path.join(R, "analise-cientifica", "cruzamento-violencia-e-severidade.json")
SAIDA = os.path.join(R, "analise-cientifica", "incerteza-da-associacao.json")
SEMENTE = 20260922
SORTEIOS = 200000


def pearson(x, y):
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def postos(x):
    ordem = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(ordem):
        j = i
        while j + 1 < len(ordem) and x[ordem[j + 1]] == x[ordem[i]]:
            j += 1
        for k in range(i, j + 1):
            r[ordem[k]] = (i + j) / 2 + 1  # empate recebe o posto medio
        i = j + 1
    return r


def spearman(x, y):
    return pearson(postos(x), postos(y))


def intervalo_fisher(r, n):
    z, ep = math.atanh(r), 1 / math.sqrt(n - 3)
    return math.tanh(z - 1.96 * ep), math.tanh(z + 1.96 * ep)


def p_permutacao(x, y, estat, rnd, sorteios=SORTEIOS):
    obs = abs(estat(x, y))
    yy, extremos = list(y), 0
    for _ in range(sorteios):
        rnd.shuffle(yy)
        if abs(estat(x, yy)) >= obs - 1e-12:
            extremos += 1
    return extremos / sorteios


def apurar():
    d = json.load(io.open(ENTRADA, encoding="utf-8"))
    anos = sorted(int(a) for a in d["serie_de_violencia"]["por_ano"])
    if anos != sorted(int(a) for a in d["serie_de_agravamento"]["por_ano"]):
        print("FALHA REAL: as duas series nao cobrem os mesmos anos")
        return 1
    v = [d["serie_de_violencia"]["por_ano"][str(a)] for a in anos]
    g = [d["serie_de_agravamento"]["por_ano"][str(a)] for a in anos]
    dv = [v[i + 1] - v[i] for i in range(len(v) - 1)]
    dg = [g[i + 1] - g[i] for i in range(len(g) - 1)]
    especificacoes = [("nivel, com tendencia", v, g),
                      ("primeira diferenca, sem tendencia", dv, dg),
                      ("primeira diferenca com defasagem de um ano", dv[:-1], dg[1:])]
    rnd = random.Random(SEMENTE)
    linhas = []
    for nome, x, y in especificacoes:
        r, s = pearson(x, y), spearman(x, y)
        lo, hi = intervalo_fisher(r, len(x))
        linhas.append({"especificacao": nome, "n": len(x), "pearson": round(r, 3),
                       "ic95_pearson": [round(lo, 3), round(hi, 3)],
                       "p_pearson_permutacao": round(p_permutacao(x, y, pearson, rnd), 3),
                       "spearman": round(s, 3),
                       "p_spearman_permutacao": round(p_permutacao(x, y, spearman, rnd), 3)})
    res = {"gerado_por": "apurar_incerteza_da_associacao.py", "janela": [anos[0], anos[-1]],
           "semente": SEMENTE, "sorteios": SORTEIOS,
           "metodo": "IC95 de Pearson pela transformacao de Fisher, aproximado com n de 12 a 14; "
                     "p bilateral por permutacao do rotulo de ano",
           "especificacoes": linhas,
           "leitura": "nenhum dos seis coeficientes se distingue de zero ao nivel de 5%"
                      if all(l["p_pearson_permutacao"] >= 0.05 and l["p_spearman_permutacao"] >= 0.05 for l in linhas)
                      else "ha coeficiente com p abaixo de 0,05; ver as linhas"}
    io.open(SAIDA + ".tmp", "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=1))
    os.replace(SAIDA + ".tmp", SAIDA)
    for l in linhas:
        print("%-45s n=%d r=%+.3f IC95=[%+.3f; %+.3f] p=%.3f | rho=%+.3f p=%.3f"
              % (l["especificacao"], l["n"], l["pearson"], l["ic95_pearson"][0], l["ic95_pearson"][1],
                 l["p_pearson_permutacao"], l["spearman"], l["p_spearman_permutacao"]))
    print(res["leitura"])
    print("gravado: " + SAIDA)
    return 0


def bancada():
    provas = []
    provas.append(("pearson de serie identica e' 1", abs(pearson([1, 2, 3, 4], [1, 2, 3, 4]) - 1) < 1e-12))
    provas.append(("pearson de serie invertida e' -1", abs(pearson([1, 2, 3, 4], [4, 3, 2, 1]) + 1) < 1e-12))
    provas.append(("empate recebe o posto medio", postos([5, 5, 1]) == [2.5, 2.5, 1.0]))
    provas.append(("spearman capta relacao monotona nao linear", abs(spearman([1, 2, 3, 4], [1, 4, 9, 100]) - 1) < 1e-12))
    lo, hi = intervalo_fisher(0.0, 28)
    provas.append(("intervalo de r = 0 e' simetrico", abs(lo + hi) < 1e-12 and lo < 0 < hi))
    rnd = random.Random(1)
    x = list(range(20))
    provas.append(("associacao perfeita da p pequeno", p_permutacao(x, x, pearson, rnd, 2000) < 0.01))
    y = [rnd.random() for _ in range(20)]
    provas.append(("serie ao acaso nao da p pequeno por construcao", p_permutacao(x, y, pearson, rnd, 2000) > 0.01))
    ok = sum(1 for _, v in provas if v)
    for nome, v in provas:
        print(("   ok    " if v else "  FALHA  ") + nome)
    print("\nBANCADA DA INCERTEZA DA ASSOCIACAO: %d de %d" % (ok, len(provas)))
    return 0 if ok == len(provas) else 1


if __name__ == "__main__":
    sys.exit(bancada() if "--bancada" in sys.argv else apurar())
