# -*- coding: utf-8 -*-
"""Refaz o teste do ciclo eleitoral sobre o UNIVERSO UNICO de 115 normas.

POR QUE EXISTE (auditoria de 16/09/2026, achado 3.2): o teste de 29/08/2026 contava as
normas pelas fichas do Legin (114 que alteram o texto), enquanto o resto do trabalho usa
a uniao Planalto e Legin (115). Dai' os numeros 114, 105 e 104 em lugares diferentes do
texto. Aqui o numerador sai de `analise-cientifica/universo-e-regimes.csv`, a mesma lista
que classifica os regimes, com a data de publicacao no DOU conferida em duas fontes.

O METODO NAO MUDA. Permutacao, poder, blocos, sorteios, semente, zero estrutural e
calendario sao os de `.claude/scripts/analise_ciclo_eleitoral_cp.py`, importado, e nao
copiado, para nao haver dois metodos que divergem em silencio.

O QUE MUDA, por decisao do autor em 18/09/2026:
  1. universo: as 115 normas; entra a Lei 6.368/1976, que o Legin nao registra;
  2. corte em 18/09/2026 (decisao do autor no mesmo dia; antes, 30/09/2026). O teste principal usa ANOS COMPLETOS, 1945 a 2025. 2026 entra
     num teste de SENSIBILIDADE com a contagem observada, sem projecao nem anualizacao:
     como 2026 e' ano de eleicao e esta' incompleto, a contagem crua SUBESTIMA o ano, e
     isso joga contra a hipotese eleitoral. O vies se declara, nao se corrige por conta;
  3. recortes por regime sem sobreposicao: ano de fronteira vai para o regime que
     governou a maior parte dele (1964 para a ditadura, 1985 para a Nova Republica), e o
     script CONFERE que toda norma daquele ano caiu de fato naquele regime pela data.
"""

import collections
import csv
import datetime as dt
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

R = os.path.dirname(os.path.abspath(__file__))
# Roda em dois lugares, e os dois se medem pela existencia da pasta, nunca se supoem:
#   no projeto, com os dados em analise-cientifica/ e o motor em ~/.claude/scripts;
#   no pacote publico (02-DADOS/scripts), com os dados em ../dados e o motor ao lado deste
#   arquivo. No pacote a saida vai para ../refeito, para nao sobrescrever o arquivo cujo
#   resumo criptografico esta' no manifesto (22/09/2026, achado da auditoria de 16/09).
NO_PROJETO = os.path.isdir(os.path.join(R, "analise-cientifica"))
DADOS = os.path.join(R, "analise-cientifica") if NO_PROJETO else os.path.join(R, os.pardir, "dados")
sys.path.insert(0, R)
sys.path.insert(1, os.path.expanduser(os.path.join("~", ".claude", "scripts")))
import analise_ciclo_eleitoral_cp as T  # noqa: E402

T.CALENDARIO = os.path.join(DADOS, "calendario-eleitoral-1940-2026.csv")
UNIVERSO = os.path.join(DADOS, "universo-e-regimes.csv")
SAIDA = (os.path.join(DADOS, "teste-ciclo-eleitoral-universo-115.json") if NO_PROJETO
         else os.path.join(R, os.pardir, "refeito", "teste-ciclo-eleitoral-universo-115.json"))
os.makedirs(os.path.dirname(SAIDA), exist_ok=True)

RECORTES = [
    (1945, 2025, T.BLOCO_PADRAO, "PRINCIPAL: anos completos, 1945 a 2025", None),
    (1945, 2026, T.BLOCO_PADRAO, "SENSIBILIDADE: com 2026 incompleto, contagem crua", None),
    (1946, 1963, 8, "Republica de 1946 (1946 a 1963)", "República de 1946"),
    (1964, 1984, 8, "Ditadura militar (1964 a 1984)", "Ditadura militar"),
    (1985, 2025, T.BLOCO_PADRAO, "Nova Republica, anos completos (1985 a 2025)", "Nova República"),
]


def main():
    with io.open(UNIVERSO, encoding="utf-8", newline="") as f:
        normas = list(csv.DictReader(f, delimiter=";"))
    if len(normas) != 115:
        print("RECUSADO: o universo tem %d normas, e nao 115" % len(normas))
        return 1
    por_ano = collections.Counter(int(n["publicacao_dou"][:4]) for n in normas)

    # a regra do ano de fronteira se confere, nao se supoe
    conflitos = []
    for ini, fim, _, nome, regime in RECORTES:
        if regime is None:
            continue
        for n in normas:
            a = int(n["publicacao_dou"][:4])
            if ini <= a <= fim and n["regime"] != regime:
                conflitos.append((nome, n["especie"], n["numero"], n["publicacao_dou"], n["regime"]))
    if conflitos:
        print("RECUSADO: norma cai em regime diferente do recorte anual:")
        for c in conflitos:
            print("   ", c)
        return 1

    cal = T.ler_calendario()
    grupos = T.grupos_de(cal)
    res = {
        "gerado_em": dt.date.today().isoformat(),
        "universo": "115 normas, analise-cientifica/universo-e-regimes.csv",
        "unidade": "ano de publicacao no DOU",
        "corte": "2026-09-18",
        "dados_ate": "2026-09-18",
        "normas_por_ano_2026": por_ano.get(2026, 0),
        "metodo": "o de analise_ciclo_eleitoral_cp.py: permutacao por blocos, %d sorteios, semente %d"
                  % (T.SORTEIOS, T.SEMENTE),
        "testes": {},
        "poder_do_desenho_principal": {},
    }
    for ini, fim, bloco, nome, _ in RECORTES:
        res["testes"][nome] = {g: T.permutacao(por_ano, anos, ini, fim, bloco) for g, anos in grupos.items()}
        print("feito: " + nome, flush=True)
    for razao in (1.0, 1.5, 2.0, 2.5, 3.0):
        res["poder_do_desenho_principal"]["razao_%s" % razao] = T.poder(
            por_ano, grupos["PRESIDENCIAL DIRETA"], 1945, 2025, razao)
    print("feito: poder", flush=True)

    tmp = SAIDA + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    os.replace(tmp, SAIDA)

    for nome, gs in res["testes"].items():
        print("=== %s ===" % nome)
        print("%-38s%5s%8s%8s%8s%8s%9s" % ("grupo", "anos", "normas", "media", "m.fora", "razao", "p"))
        for g, r in gs.items():
            if not r.get("examinavel"):
                print("%-38s%5s   nao examinavel (%s anos no grupo)" % (g, r["anos_COM_pleito"], r["anos_COM_pleito"]))
                continue
            print("%-38s%5d%8d%8s%8s%8s%9s" % (g, r["anos_COM_pleito"], r["normas_no_grupo"], r["media_no_grupo"],
                                              r["media_fora"], r["razao"], r["p_valor_bilateral"]))
        tot = next(iter(gs.values()))["normas_no_recorte"]
        print("normas no recorte: %d" % tot)
    print("PODER, presidencial direta, 1945 a 2025: %s" % res["poder_do_desenho_principal"])
    print("gravado: " + SAIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
