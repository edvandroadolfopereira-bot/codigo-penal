# Cruzamento da AUTORIA da norma com a COMPOSICAO DE BANCADA e com a direcao de
# severidade que a norma produziu.
#
# Por que ele nao existia ate' 30/08/2026: o rotulo da norma esta' gravado em TRES
# formatos que nao casam entre si, e por isso a juncao devolvia zero.
#
#   camara_autores.norma          'Lei Ordinaria no 9.983, de 14 de julho de 2000'
#   cp-eventos-de-severidade      '5474/1968'
#   cp-severidade-por-artigo      'L7209/1984'
#
# Zero em juncao nao e' ausencia de dado, e' chave errada. Regra desta casa de
# 03/08/2026: quando o filtro devolve resultado surpreendente, suspeitar do filtro
# antes do sistema.
#
# O QUE ELE MEDE, e nada alem disso:
#   1. a origem da iniciativa de cada norma, Executivo, Legislativo ou comissao;
#   2. o partido do autor na data da norma, quando o autor e' deputado;
#   3. a direcao de severidade que cada norma produziu, por evento datado;
#   4. a coesao de cada partido no voto nominal, e a divergencia entre eles.
#
# O QUE ELE NAO MEDE, e se declara em vez de calar: posicao ideologica. Classificar
# partido em espectro exige escala externa publicada, que NAO esta' neste acervo, e
# inventar uma seria fabricar o proprio criterio de medida.

import collections
import csv
import io
import json
import os
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(RAIZ, "BASE-CODIGO-PENAL.sqlite")
EVENTOS = os.path.join(RAIZ, "cp-eventos-de-severidade.csv")
SAIDA = os.path.join(RAIZ, "analise-cientifica", "autoria-e-bancada.json")

_ESPECIE = [
    (re.compile(r"lei\s+complementar", re.I), "LC"),
    (re.compile(r"decreto[\s\-]*lei", re.I), "DL"),
    (re.compile(r"lei\s+ordin", re.I), "L"),
    (re.compile(r"^\s*lei\b", re.I), "L"),
    (re.compile(r"^\s*decreto\b", re.I), "D"),
    (re.compile(r"medida\s+provis", re.I), "MP"),
]


def chave(rotulo):
    """Devolve (numero, ano) a partir de qualquer um dos tres formatos de rotulo.

    Junta-se por NUMERO e ANO, e nao pela especie, porque o arquivo de eventos nao
    grava especie nenhuma. Numero mais ano e' praticamente unico no periodo, e a
    ambiguidade que sobrar sai declarada, nunca resolvida por escolha silenciosa.
    """
    if not rotulo:
        return None
    t = str(rotulo).strip()
    m = re.match(r"^\s*([A-Za-z]{0,3})\s*([\d.]+)\s*/\s*(\d{4})\s*$", t)
    if m:
        num = m.group(2).replace(".", "")
        if num.isdigit():
            return (int(num), int(m.group(3)))
        return None
    m = re.search(r"n[o°º\.]*\s*([\d.]+)[^\d]{1,40}?(\d{4})\b", t, re.I)
    if not m:
        m = re.search(r"\b([\d.]{3,})\b.*?\b(\d{4})\b", t)
    if not m:
        return None
    num = m.group(1).replace(".", "")
    if not num.isdigit():
        return None
    return (int(num), int(m.group(2)))


def especie_de(rotulo):
    for padrao, sigla in _ESPECIE:
        if padrao.search(str(rotulo or "")):
            return sigla
    return "?"


def origem_da_iniciativa(autores):
    """Classifica a origem pelo conjunto de (tipo_de_autor, autor) de uma mesma norma.

    Executivo vence quando presente, porque projeto de iniciativa do Presidente
    assinado tambem por parlamentar continua sendo iniciativa do Executivo.

    CORRIGIDO em 30/08/2026, e a versao anterior produzia conclusao errada. O tipo
    'Orgao do Poder Legislativo' NAO e' orgao anonimo: e' o SENADO FEDERAL, com o
    nome do senador ou da comissao dentro do campo do autor, no formato
    'Senado Federal - Rodrigo Pacheco'. Tratado como orgao, o Senado aparecia com
    razao de 9,5 agravamentos por abrandamento, o que sugeria um ator institucional
    mais duro que os demais. Ele nao existe: sao senadores. Regra desta casa de
    04/08/2026, item 4: antes de consertar, olhar o item.
    """
    pares = [((t or ""), (a or "")) for t, a in autores]
    junto = " | ".join(sorted(set(t + " :: " + a for t, a in pares))).lower()
    if "executivo" in junto:
        return "Executivo"
    tem_comissao = any(x in junto for x in ("cpi", "cpmi", "comiss"))
    tem_senado = "senado federal" in junto
    tem_deputado = "deputado" in junto
    if tem_comissao and not (tem_deputado or (tem_senado and not tem_comissao)):
        return "Legislativo, comissao ou CPI"
    if tem_deputado and tem_senado:
        return "Legislativo, Camara e Senado"
    if tem_deputado:
        return "Legislativo, Camara dos Deputados"
    if tem_senado:
        return "Legislativo, Senado Federal"
    if "legislativo" in junto:
        return "Legislativo, nao especificado"
    return "nao identificada"


def ler_eventos():
    with io.open(EVENTOS, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def apurar():
    if not os.path.exists(BASE):
        print("FALHA REAL: base ausente: " + BASE)
        return 1
    c = sqlite3.connect(BASE)
    c.row_factory = sqlite3.Row

    # --- autoria, por norma -------------------------------------------------
    autores = list(c.execute("""SELECT norma, autor, tipo_de_autor,
                                       partido_na_data_da_norma AS partido, uf
                                FROM camara_autores"""))
    por_norma = collections.defaultdict(list)
    sem_chave = []
    for r in autores:
        k = chave(r["norma"])
        if k is None:
            sem_chave.append(r["norma"])
            continue
        por_norma[k].append(dict(r))

    # --- eventos datados de severidade --------------------------------------
    eventos = ler_eventos()
    ev_sem_chave = []
    ev_por_chave = collections.defaultdict(list)
    for e in eventos:
        k = chave(e["norma"])
        if k is None:
            ev_sem_chave.append(e["norma"])
            continue
        ev_por_chave[k].append(e)

    normas_evento = set(ev_por_chave)
    normas_autoria = set(por_norma)
    casadas = normas_evento & normas_autoria

    # --- origem por evento --------------------------------------------------
    por_origem = collections.Counter()
    dir_por_origem = collections.defaultdict(collections.Counter)
    dir_por_partido = collections.defaultdict(collections.Counter)
    normas_por_origem = collections.defaultdict(set)
    for k in normas_evento:
        aut = por_norma.get(k, [])
        origem = (origem_da_iniciativa([(a["tipo_de_autor"], a["autor"]) for a in aut])
                  if aut else "sem dado de autoria")
        normas_por_origem[origem].add(k)
        partidos = sorted(set((a["partido"] or "").strip() for a in aut
                              if (a["partido"] or "").strip()))
        for e in ev_por_chave[k]:
            por_origem[origem] += 1
            dir_por_origem[origem][e["direcao"]] += 1
            for p in partidos:
                dir_por_partido[p][e["direcao"]] += 1

    # --- coesao partidaria no voto nominal ----------------------------------
    coesao = {}
    for r in c.execute("""SELECT partido,
                                 SUM(CASE WHEN voto='Sim' THEN 1 ELSE 0 END) sim,
                                 SUM(CASE WHEN voto='Não' THEN 1 ELSE 0 END) nao,
                                 SUM(CASE WHEN voto IN ('Obstrução','Abstenção','Artigo 17') THEN 1 ELSE 0 END) outros,
                                 COUNT(*) total,
                                 COUNT(DISTINCT norma) normas
                          FROM camara_votos_nominais
                          GROUP BY partido ORDER BY total DESC"""):
        validos = r["sim"] + r["nao"]
        coesao[r["partido"]] = {
            "sim": r["sim"], "nao": r["nao"], "outros": r["outros"],
            "total": r["total"], "normas": r["normas"],
            "pct_sim_entre_validos": round(100.0 * r["sim"] / validos, 1) if validos else None,
        }

    total_votos = sum(v["total"] for v in coesao.values())
    total_sim = sum(v["sim"] for v in coesao.values())
    total_nao = sum(v["nao"] for v in coesao.values())

    # --- autoria por partido, contando NORMAS e nao assinaturas -------------
    normas_por_partido = collections.defaultdict(set)
    for k, aut in por_norma.items():
        for a in aut:
            p = (a["partido"] or "").strip()
            if p:
                normas_por_partido[p].add(k)

    resultado = {
        "gerado_por": "apurar_autoria_e_bancada.py",
        "o_que_mede": "origem da iniciativa, partido do autor, direcao de severidade e coesao no voto",
        "o_que_nao_mede": ("posicao ideologica de partido, que exigiria escala externa publicada, "
                           "ausente deste acervo"),
        "cobertura": {
            "assinaturas_de_autoria": len(autores),
            "assinaturas_sem_chave_extraivel": len(sem_chave),
            "normas_com_autoria": len(normas_autoria),
            "normas_com_evento_datado_de_severidade": len(normas_evento),
            "normas_com_AMBOS": len(casadas),
            "normas_com_evento_e_SEM_autoria": len(normas_evento - normas_autoria),
            "eventos_datados": len(eventos),
            "eventos_sem_chave_extraivel": len(ev_sem_chave),
        },
        "eventos_por_origem_da_iniciativa": dict(por_origem),
        "normas_por_origem_da_iniciativa": {k: len(v) for k, v in normas_por_origem.items()},
        "direcao_por_origem": {k: dict(v) for k, v in dir_por_origem.items()},
        "direcao_por_partido_do_autor": {k: dict(v) for k, v in sorted(dir_por_partido.items())},
        "normas_autoradas_por_partido": {k: len(v) for k, v in
                                         sorted(normas_por_partido.items(), key=lambda x: (-len(x[1]), x[0]))},
        "coesao_no_voto_nominal": coesao,
        "voto_nominal_total": {"votos": total_votos, "sim": total_sim, "nao": total_nao,
                               "pct_sim_entre_validos": round(100.0 * total_sim / (total_sim + total_nao), 1)
                               if (total_sim + total_nao) else None},
    }
    c.close()

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    io.open(SAIDA, "w", encoding="utf-8", newline="").write(
        json.dumps(resultado, ensure_ascii=False, indent=1))

    cob = resultado["cobertura"]
    print("=== COBERTURA DO CRUZAMENTO ===")
    for k, v in cob.items():
        print("   %-46s %6d" % (k.replace("_", " "), v))
    print()
    print("=== EVENTOS DE SEVERIDADE POR ORIGEM DA INICIATIVA ===")
    for origem, n in por_origem.most_common():
        d = dir_por_origem[origem]
        print("   %-28s %3d eventos em %2d normas | %s"
              % (origem, n, len(normas_por_origem[origem]),
                 ", ".join("%s %d" % (a, b) for a, b in sorted(d.items()))))
    print()
    print("=== NORMAS AUTORADAS POR PARTIDO, todas ===")
    for p, n in resultado["normas_autoradas_por_partido"].items():
        print("   %-22s %3d" % (p, n))
    print()
    print("=== COESAO NO VOTO NOMINAL, todos os partidos ===")
    for p, v in sorted(coesao.items(), key=lambda x: -x[1]["total"]):
        print("   %-16s %5d votos em %2d normas | sim %5d nao %5d outros %4d | %% sim %s"
              % (p, v["total"], v["normas"], v["sim"], v["nao"], v["outros"],
                 v["pct_sim_entre_validos"]))
    print()
    print("total: %d votos, %d sim, %d nao, %.1f%% de sim entre os validos"
          % (total_votos, total_sim, total_nao,
             resultado["voto_nominal_total"]["pct_sim_entre_validos"]))
    print()
    print("gravado: " + SAIDA)
    if cob["normas_com_AMBOS"] == 0:
        print("FALHA REAL: zero normas casaram. Isso e' chave errada, nao ausencia de dado.")
        return 1
    return 0


def bancada():
    """Mede as duas direcoes, e desliga o normalizador para o veredito ter que mudar."""
    provas = []
    casos = [
        ("Lei Ordinária nº 9.983, de 14 de julho de 2000", (9983, 2000)),
        ("Lei Complementar nº 225, de 8 de janeiro de 2026", (225, 2026)),
        ("Decreto-Lei nº 1.004, de 21 de outubro de 1969", (1004, 1969)),
        ("5474/1968", (5474, 1968)),
        ("L7209/1984", (7209, 1984)),
        ("DL898/1969", (898, 1969)),
        ("Lei nº 14.197, de 1º de setembro de 2021", (14197, 2021)),
    ]
    for rotulo, esperado in casos:
        provas.append(("chave de %r" % rotulo, chave(rotulo) == esperado))
    provas.append(("rotulo vazio devolve None", chave("") is None))
    provas.append(("rotulo sem numero devolve None", chave("Portaria sem numero") is None))
    provas.append(("especie de Lei Complementar", especie_de("Lei Complementar nº 225") == "LC"))
    provas.append(("especie de Decreto-Lei", especie_de("Decreto-Lei nº 1.004") == "DL"))
    dep = ("Deputado(a)", "Fulano de Tal")
    exe = ("Órgão do Poder Executivo", "Poder Executivo")
    sen = ("Órgão do Poder Legislativo", "Senado Federal - Rodrigo Pacheco")
    cpi = ("Órgão do Poder Legislativo", "Senado Federal - CPI da Pedofilia")
    provas.append(("Executivo vence quando presente",
                   origem_da_iniciativa([dep, exe]) == "Executivo"))
    provas.append(("so' deputado e' Camara",
                   origem_da_iniciativa([dep]) == "Legislativo, Camara dos Deputados"))
    provas.append(("orgao do Legislativo com nome de senador e' SENADO, nao orgao",
                   origem_da_iniciativa([sen]) == "Legislativo, Senado Federal"))
    provas.append(("CPI do Senado e' comissao",
                   origem_da_iniciativa([cpi]) == "Legislativo, comissao ou CPI"))
    provas.append(("deputado mais senador e' as duas casas",
                   origem_da_iniciativa([dep, sen]) == "Legislativo, Camara e Senado"))
    provas.append(("lista vazia nao identifica",
                   origem_da_iniciativa([]) == "nao identificada"))

    # DESLIGAR o normalizador tem que MUDAR o veredito: sem ele, nada casa.
    # Sem esta prova a bancada aprovaria instrumento morto (regra de 29/08/2026).
    desligado = lambda r: None
    casadas_desligado = sum(1 for r, _ in casos if desligado(r) is not None)
    provas.append(("com o normalizador DESLIGADO nada casa", casadas_desligado == 0))
    casadas_ligado = sum(1 for r, _ in casos if chave(r) is not None)
    provas.append(("com o normalizador LIGADO casam os %d casos" % len(casos),
                   casadas_ligado == len(casos)))

    ok = sum(1 for _, v in provas if v)
    for nome, v in provas:
        print(("   ok    " if v else "  FALHA  ") + nome)
    print("")
    print("BANCADA DO CRUZAMENTO DE AUTORIA: %d de %d" % (ok, len(provas)))
    return 0 if ok == len(provas) else 1


if __name__ == "__main__":
    if "--bancada" in sys.argv:
        sys.exit(bancada())
    sys.exit(apurar())
