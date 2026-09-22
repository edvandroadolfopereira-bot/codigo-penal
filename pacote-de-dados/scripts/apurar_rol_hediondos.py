# -*- coding: utf-8 -*-
# O AGRAVAMENTO FEITO FORA DO TEXTO DO CODIGO, medido como SEGUNDA UNIDADE.
#
# POR QUE ELE EXISTE: a regua de severidade deste trabalho mede a faixa de pena
# cominada NO TEXTO DO CODIGO. Um artigo pode ficar mais severo sem que uma virgula
# do seu texto mude, bastando que ele entre no rol de crimes hediondos da Lei n.
# 8.072, de 1990, que veda progressao, fianca, graca e indulto e dobra a fracao
# exigida para o livramento condicional.
#
# O QUE ELE MEDE, e sao tres coisas:
#   1. quantas normas tocaram o rol, e quantas delas o trabalho ja' media;
#   2. quantos dos artigos do rol a regua do texto ja' alcanca por outro caminho;
#   3. o TAMANHO do agravamento, em parametro comparavel ao da regua da Parte Geral.
#
# O TERCEIRO PONTO E' O QUE FALTAVA. Ate' aqui o item de alcance dizia que a
# severidade "pode subir sem que o texto seja tocado", sem dizer QUANTO. Com o texto
# da Lei 8.072 e o do Codigo lado a lado, o quanto se mede.
#
# LIMITE QUE ACOMPANHA, e ele muda o que se pode afirmar do parametro vigente: o
# paragrafo 2 do art. 2 da Lei 8.072, que fixava a progressao em 2/5 e 3/5, foi
# REVOGADO pela Lei n. 13.964, de 2019, que remeteu a materia ao art. 112 da Lei de
# Execucao Penal. O parametro de progressao vigente esta' FORA do recorte deste
# trabalho, e por isso entra declarado como historico, e nao como vigente.

import collections
import io
import json
import os
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

R = os.path.dirname(os.path.abspath(__file__))
ROL = os.path.join(R, "analise-cientifica", "rol-hediondos.json")
EVENTOS = os.path.join(R, "cp-eventos-de-severidade.csv")
PLANALTO = os.path.join(R, "textos-das-normas", "texto-integral-planalto.jsonl")
CP = os.path.join(R, "cp-compilado-texto.txt")
BASE = os.path.join(R, "BASE-CODIGO-PENAL.sqlite")
SAIDA = os.path.join(R, "analise-cientifica", "rol-como-segunda-unidade.json")

RE_DISP = re.compile(r"(?:art\.?\s*)?(\d+)(?:-([A-Z])(?![A-Za-zÀ-ÿ]))?", re.I)
RE_NORMA = re.compile(r"Lei\s+([\d.]+)/(\d{4})")


def designacao(m):
    return "%s-%s" % (m.group(1), m.group(2)) if m.group(2) else m.group(1)


def artigo_de(d):
    m = RE_DISP.search(str(d or ""))
    return designacao(m) if m else None


def texto_da_lei(numero, ano):
    """Le o texto integral de uma norma do arquivo colhido no Planalto."""
    if not os.path.exists(PLANALTO):
        return None
    with io.open(PLANALTO, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            o = json.loads(ln)
            if str(o.get("numero")) == str(numero) and str(o.get("ano")) == str(ano):
                return o.get("texto")
    return None


# Cada parametro declara ONDE procurar e o que a diferenca significa. O valor sai do
# texto, e nunca digitado aqui, pela mesma disciplina da regua da Parte Geral.
PARAMETROS = [
    {"parametro": "Livramento condicional, fracao exigida do primario",
     "comum": ("CP", r"I - cumprida mais de (um ter[cç]o) da pena"),
     "hediondo": ("CP", r"cumpridos mais de (dois ter[cç]os) da pena, nos casos\s*de condena[cç][ãa]o por crime hediondo"),
     "porque": "fracao maior obriga a cumprir mais antes de sair",
     "vigente": True},
    {"parametro": "Progressao de regime, fracao do primario",
     "comum": (None, None),
     "hediondo": ("8072", r"dar-se-[áa] ap[óo]s o cumprimento de (2/5)"),
     "porque": ("parametro HISTORICO: o paragrafo que o fixava foi revogado pela Lei "
                "13.964/2019, que remeteu a materia ao art. 112 da Lei de Execucao Penal"),
     "vigente": False},
    {"parametro": "Progressao de regime, fracao do reincidente",
     "comum": (None, None),
     "hediondo": ("8072", r"e de (3/5)"),
     "porque": "mesmo parametro historico, para o reincidente",
     "vigente": False},
]

VEDACOES = [
    {"vedacao": "anistia, graca e indulto", "onde": r"I - anistia, gra[cç]a e indulto"},
    {"vedacao": "fianca", "onde": r"II - fian[cç]a"},
    {"vedacao": "regime inicial obrigatoriamente fechado",
     "onde": r"ser[áa] cumprida inicialmente em regime fechado"},
]


def apurar():
    for p in (ROL, EVENTOS, PLANALTO, CP, BASE):
        if not os.path.exists(p):
            print("FALHA REAL: falta " + p)
            return 1
    rol = json.load(io.open(ROL, encoding="utf-8"))
    cp = re.sub(r"\s+", " ", io.open(CP, encoding="utf-8").read())
    l8072 = texto_da_lei("8072", "1990")
    if not l8072:
        print("FALHA REAL: o texto da Lei 8.072/1990 nao esta' no arquivo do Planalto.")
        return 1
    l8072 = re.sub(r"\s+", " ", l8072)

    c = sqlite3.connect(BASE)
    das115 = set((int(str(r[1]).replace(".", "")), int(r[2]))
                 for r in c.execute("SELECT especie, numero, ano FROM uniao_normas_alteradoras"))
    elei = set(int(r[0]) for r in c.execute("SELECT ano FROM calendario_eleitoral_tse"))
    c.close()

    # --- 1. as normas que tocaram o rol -------------------------------------
    por_norma = collections.Counter()
    for x in rol["detalhe"]:
        por_norma[x["ultima_redacao"]] += 1
    normas = []
    for n, q in sorted(por_norma.items(), key=lambda kv: int(RE_NORMA.match(kv[0]).group(2))):
        m = RE_NORMA.match(n)
        num, ano = int(m.group(1).replace(".", "")), int(m.group(2))
        normas.append({"norma": n, "numero": num, "ano": ano, "artigos": q,
                       "entre_as_115": (num, ano) in das115,
                       "ano_eleitoral": ano in elei})
    fora = [x for x in normas if not x["entre_as_115"]]

    # --- 2. sobreposicao com a regua do texto -------------------------------
    with io.open(EVENTOS, encoding="utf-8", newline="") as f:
        import csv as _csv
        ev = list(_csv.DictReader(f, delimiter=";"))
    arts_ev = collections.Counter()
    for e in ev:
        a = artigo_de(e["dispositivo"])
        if a:
            arts_ev[a] += 1
    sobre = []
    for x in rol["detalhe"]:
        sobre.append({"artigo": x["artigo"], "crime": x["crime"],
                      "eventos_no_texto": arts_ev.get(x["artigo"], 0)})
    invisiveis = [x for x in sobre if x["eventos_no_texto"] == 0]

    # --- 3. o TAMANHO do agravamento ----------------------------------------
    fontes = {"CP": cp, "8072": l8072}
    medidos, nao_lidos = [], []
    for p in PARAMETROS:
        vals = {}
        for lado in ("comum", "hediondo"):
            onde, padrao = p[lado]
            if onde is None:
                vals[lado] = None
                continue
            m = re.search(padrao, fontes[onde], re.I)
            vals[lado] = m.group(1) if m else "NAO LIDO"
            if vals[lado] == "NAO LIDO":
                nao_lidos.append({"parametro": p["parametro"], "lado": lado})
        medidos.append({"parametro": p["parametro"], "porque": p["porque"],
                        "vigente": p["vigente"],
                        "no_regime_comum": vals["comum"], "no_rol": vals["hediondo"]})
    vedacoes = []
    for v in VEDACOES:
        achou = re.search(v["onde"], l8072, re.I)
        vedacoes.append({"vedacao": v["vedacao"], "consta_na_lei": bool(achou),
                         "trecho": achou.group(0) if achou else None})
        if not achou:
            nao_lidos.append({"parametro": v["vedacao"], "lado": "8072"})

    res = {
        "gerado_por": "apurar_rol_hediondos.py",
        "o_que_mede": ("o agravamento produzido FORA do texto do Codigo Penal, pela inclusao "
                       "do artigo no rol de crimes hediondos"),
        "fonte_do_rol": rol["fonte"], "fonte_do_texto": "texto-integral-planalto.jsonl",
        "normas_que_tocaram_o_rol": normas,
        "normas_fora_das_115": [x["norma"] for x in fora],
        "artigos_afetados_por_norma_fora_das_115": sum(x["artigos"] for x in fora),
        "sobreposicao_com_a_regua_do_texto": sobre,
        "artigos_do_rol_invisiveis_para_a_regua": invisiveis,
        "parametros_medidos": medidos,
        "vedacoes": vedacoes,
        "parametros_nao_lidos": nao_lidos,
        "limite_declarado": rol["limite_declarado"],
    }
    io.open(SAIDA, "w", encoding="utf-8", newline="").write(
        json.dumps(res, ensure_ascii=False, indent=1))

    print("=== 1. AS NORMAS QUE TOCARAM O ROL ===")
    print("%-22s %5s %6s %-16s %s" % ("norma", "arts", "ano", "entre as 115?", "ano eleitoral?"))
    for x in normas:
        print("%-22s %5d %6d %-16s %s" % (x["norma"], x["artigos"], x["ano"],
              "sim" if x["entre_as_115"] else "NAO", "sim" if x["ano_eleitoral"] else "nao"))
    print()
    print("   normas fora das 115: %d, afetando %d artigo(s)"
          % (len(fora), sum(x["artigos"] for x in fora)))
    print()
    print("=== 2. SOBREPOSICAO COM A REGUA DO TEXTO ===")
    print("   artigos do rol com evento datado no texto : %d de %d"
          % (len(sobre) - len(invisiveis), len(sobre)))
    print("   artigos INVISIVEIS para a regua do texto  : %d" % len(invisiveis))
    for x in invisiveis:
        print("      art. %s, %s" % (x["artigo"], x["crime"]))
    print()
    print("=== 3. O TAMANHO DO AGRAVAMENTO, em parametro comparavel ===")
    print("%-52s %-16s %-16s %s" % ("parametro", "regime comum", "no rol", "vigente?"))
    for m in medidos:
        print("%-52s %-16s %-16s %s" % (m["parametro"][:52],
              m["no_regime_comum"] if m["no_regime_comum"] else "nao se aplica",
              m["no_rol"] if m["no_rol"] else "nao lido",
              "sim" if m["vigente"] else "HISTORICO"))
    print()
    print("   vedacoes que a entrada no rol impoe, lidas do texto da Lei 8.072:")
    for v in vedacoes:
        print("      %-44s %s" % (v["vedacao"], "consta" if v["consta_na_lei"] else "NAO ACHADA"))
    print()
    print("gravado: " + SAIDA)
    if nao_lidos:
        print("ATENCAO: %d parametro(s) NAO lido(s) do texto. Isso e' ausencia de medicao."
              % len(nao_lidos))
        for x in nao_lidos:
            print("   %s, lado %s" % (x["parametro"], x["lado"]))
        return 1
    return 0


def bancada():
    provas = []
    provas.append(("dispositivo simples", artigo_de("art. 157") == "157"))
    provas.append(("dispositivo com sufixo", artigo_de("art. 121-A") == "121-A"))
    provas.append(("hifen separador nao vira sufixo", artigo_de("Art. 33 - A pena") == "33"))
    provas.append(("sem numero devolve None", artigo_de("caput") is None))

    cp = ("I - cumprida mais de um terço da pena se o condenado nao for reincidente "
          "V - cumpridos mais de dois terços da pena, nos casos de condenação por crime "
          "hediondo, prática de tortura")
    m1 = re.search(r"I - cumprida mais de (um ter[cç]o) da pena", cp, re.I)
    m2 = re.search(r"cumpridos mais de (dois ter[cç]os) da pena, nos casos\s*de condena[cç][ãa]o por crime hediondo", cp, re.I)
    provas.append(("le a fracao do primario comum", m1 and m1.group(1) == "um terço"))
    provas.append(("le a fracao do hediondo", m2 and m2.group(1) == "dois terços"))

    l = ("Art. 2º Os crimes hediondos sao insuscetiveis de: I - anistia, graça e indulto; "
         "II - fiança. § 1 o A pena por crime previsto neste artigo será cumprida "
         "inicialmente em regime fechado. § 2 o A progressão de regime dar-se-á após o "
         "cumprimento de 2/5 (dois quintos) da pena, se o apenado for primário, e de 3/5 "
         "(três quintos), se reincidente.")
    for v in VEDACOES:
        provas.append(("acha a vedacao de " + v["vedacao"], bool(re.search(v["onde"], l, re.I))))
    provas.append(("le a progressao de 2/5", re.search(r"cumprimento de (2/5)", l).group(1) == "2/5"))
    provas.append(("le a progressao de 3/5", re.search(r"e de (3/5)", l).group(1) == "3/5"))

    # o texto que NAO tem o parametro tem que devolver ausencia, e nao valor
    provas.append(("texto sem a vedacao devolve ausencia",
                   re.search(VEDACOES[0]["onde"], "texto qualquer sem nada disso", re.I) is None))
    ok = sum(1 for _, v in provas if v)
    for nome, v in provas:
        print(("   ok    " if v else "  FALHA  ") + nome)
    print("")
    print("BANCADA DO ROL DE HEDIONDOS: %d de %d" % (ok, len(provas)))
    return 0 if ok == len(provas) else 1


if __name__ == "__main__":
    sys.exit(bancada() if "--bancada" in sys.argv else apurar())
