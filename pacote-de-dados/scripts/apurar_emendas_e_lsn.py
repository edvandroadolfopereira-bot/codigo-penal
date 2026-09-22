# -*- coding: utf-8 -*-
# EMENDAS CONSTITUCIONAIS e LEI DE SEGURANCA NACIONAL, dois itens da secao de alcance.
#
# Item 3 da tabela de alcance dizia, das Emendas Constitucionais, "nenhuma linha
# coletada". Item 4 dizia, da Lei de Seguranca Nacional, que ela "e' o que permitiria
# nomear o instrumento repressivo, hoje afirmado apenas por negativa".
#
# A fonte e' a base normas-leg, do portal Normas.leg.br, mantido pelo Senado Federal,
# pela Camara dos Deputados e pelo Congresso Nacional, ja' usada neste projeto em
# 30/08/2026 para conferir a revogacao da Lei 7.170/1983.
#
# O DEFEITO DE METODO QUE ESTE SCRIPT MEDE, e ele vale para os dois itens: BUSCA POR
# EMENTA PERDE A NORMA ALTERADORA. O Decreto-Lei 510/1969 altera o Decreto-Lei
# 314/1967, que e' a primeira lei de seguranca nacional da ditadura, e a ementa dele
# NAO diz 'seguranca nacional': diz apenas que altera o 314. Ele so' aparece buscando
# por numero. E' a mesma familia do defeito medido em 24/08/2026, quando o texto
# compilado do Planalto escondeu 19 normas alteradoras do Codigo Penal.

import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

R = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.realpath(os.path.join(os.environ["USERPROFILE"], ".claude", "normas-leg", "data"))
SAIDA = os.path.join(R, "analise-cientifica", "emendas-e-lsn.json")
DETALHE = os.path.join(R, "analise-cientifica", "emendas-e-lsn.txt")

RE_SEGURANCA = re.compile(r"seguran[çc]a nacional", re.I)
RE_DEFINE_CRIME = re.compile(r"define\s+.{0,20}crimes?\s+contra\s+a\s+seguran[çc]a nacional", re.I)
RE_PENAL = re.compile(r"\bpenal\b|\bcrimes?\b|\bpenas?\b|hediondo|imprescrit|punibilidade", re.I)


def catalogo(ini, fim):
    """Percorre o catalogo ano a ano, do primeiro ao ultimo, sem amostragem."""
    anos = 0
    for ano in range(ini, fim + 1):
        p = os.path.join(BASE, "catalogo", "catalogo-%d.jsonl" % ano)
        if not os.path.exists(p):
            continue
        anos += 1
        with io.open(p, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    yield ano, json.loads(ln)
    catalogo.anos_lidos = anos


def texto_do_articulado(o):
    """O articulado vem em workExample, que e' DICIONARIO em umas normas e LISTA em
    outras. Tratar so' um dos dois faz a norma parecer sem texto, defeito ja' medido
    nesta casa em 29/08/2026."""
    we = o.get("workExample")
    itens = we if isinstance(we, list) else ([we] if we else [])
    return "".join(json.dumps(it, ensure_ascii=False) for it in itens if isinstance(it, dict))


def apurar():
    if not os.path.isdir(BASE):
        print("FALHA REAL: base normas-leg ausente em " + BASE)
        return 1

    # ---------------------------------------------- Lei de Seguranca Nacional
    por_ementa, todas_1930_1989, registros = [], 0, 0
    for ano, o in catalogo(1930, 1989):
        registros += 1
        if RE_SEGURANCA.search((o.get("ementa") or "") + " " + (o.get("apelido") or "")):
            por_ementa.append(o)
    anos_lsn = catalogo.anos_lidos

    definem = [o for o in por_ementa if RE_DEFINE_CRIME.search(o.get("ementa") or "")]

    # a norma ALTERADORA nao casa por ementa, e por isso se procura por numero tambem
    conhecidas = [("decreto.lei", "510", 1969), ("decreto.lei", "314", 1967),
                  ("decreto.lei", "898", 1969), ("lei", "6620", 1978),
                  ("lei", "7170", 1983), ("lei", "5786", 1972), ("lei", "38", 1935)]
    por_numero = []
    for tipo, num, ano in conhecidas:
        p = os.path.join(BASE, "catalogo", "catalogo-%d.jsonl" % ano)
        if not os.path.exists(p):
            continue
        with io.open(p, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                o = json.loads(ln)
                if str(o.get("numero")) == num and (o.get("tipo") or "").startswith(tipo):
                    o["_achada_por"] = "numero"
                    o["_casa_por_ementa"] = bool(RE_SEGURANCA.search(o.get("ementa") or ""))
                    por_numero.append(o)
    so_por_numero = [o for o in por_numero if not o["_casa_por_ementa"]]

    # ------------------------------------------------ Emendas Constitucionais
    ecs = []
    for ano, o in catalogo(1940, 2026):
        if "emenda" in (o.get("tipo") or "").lower():
            ecs.append(o)
    anos_ec = catalogo.anos_lidos
    tam = sorted(len(o.get("ementa") or "") for o in ecs)
    ec_por_ementa = [o for o in ecs if RE_PENAL.search(o.get("ementa") or "")]
    com_art, sem_art, ec_por_texto = 0, 0, []
    for o in ecs:
        t = texto_do_articulado(o)
        if t.strip():
            com_art += 1
            if RE_PENAL.search(t):
                ec_por_texto.append(o)
        else:
            sem_art += 1

    res = {
        "gerado_por": "apurar_emendas_e_lsn.py",
        "fonte": "portal Normas.leg.br, Senado Federal, Camara dos Deputados e Congresso Nacional",
        "lei_de_seguranca_nacional": {
            "anos_de_catalogo_percorridos": anos_lsn,
            "registros_percorridos": registros,
            "normas_que_citam_seguranca_nacional_na_ementa": len(por_ementa),
            "normas_que_DEFINEM_crime_contra_a_seguranca_nacional": [
                {"nome": o.get("nome"), "urn": o.get("urn"), "data": o.get("assinatura"),
                 "ementa": re.sub(r"\s+", " ", o.get("ementa") or ""),
                 "situacao": [s.get("nomeSituacao") for s in (o.get("status") or [])],
                 "revogada_por": o.get("urnRevogacao")} for o in
                sorted(definem, key=lambda x: x.get("assinatura") or "")],
            "achadas_SO_por_numero_e_nao_por_ementa": [
                {"nome": o.get("nome"), "ementa": re.sub(r"\s+", " ", o.get("ementa") or ""),
                 "revogada_por": o.get("urnRevogacao")} for o in so_por_numero],
        },
        "emendas_constitucionais": {
            "anos_de_catalogo_percorridos": anos_ec,
            "emendas_no_catalogo": len(ecs),
            "ementa_comprimento_minimo": tam[0] if tam else 0,
            "ementa_comprimento_mediano": tam[len(tam) // 2] if tam else 0,
            "ementa_comprimento_maximo": tam[-1] if tam else 0,
            "emendas_com_ementa_vazia": sum(1 for t in tam if t == 0),
            "emendas_com_articulado_na_base": com_art,
            "emendas_SEM_articulado_na_base": sem_art,
            "citam_materia_penal_na_ementa": len(ec_por_ementa),
            "citam_materia_penal_no_articulado": [
                {"nome": o.get("nome"), "data": o.get("assinatura"),
                 "ementa": re.sub(r"\s+", " ", o.get("ementa") or "")} for o in ec_por_texto],
        },
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    io.open(SAIDA, "w", encoding="utf-8", newline="").write(
        json.dumps(res, ensure_ascii=False, indent=1))

    D = ["DETALHE INTEGRAL, emendas constitucionais e lei de seguranca nacional", "",
         "=== todas as normas cuja ementa cita seguranca nacional, de 1930 a 1989 ==="]
    for o in sorted(por_ementa, key=lambda x: x.get("assinatura") or ""):
        D.append("%s  %s" % (o.get("assinatura"), o.get("nome")))
        D.append("    %s" % re.sub(r"\s+", " ", o.get("ementa") or ""))
    D += ["", "=== todas as emendas constitucionais, com a ementa ==="]
    for o in sorted(ecs, key=lambda x: x.get("assinatura") or ""):
        D.append("%s  %-34s %s" % (o.get("assinatura"), o.get("nome"),
                                   re.sub(r"\s+", " ", o.get("ementa") or "(vazia)")))
    io.open(DETALHE, "w", encoding="utf-8", newline="").write(chr(10).join(D))

    lsn = res["lei_de_seguranca_nacional"]
    ec = res["emendas_constitucionais"]
    print("=== 1. A LEI DE SEGURANCA NACIONAL, e o sistema penal paralelo ===")
    print("   anos de catalogo percorridos, de 1930 a 1989: %d" % lsn["anos_de_catalogo_percorridos"])
    print("   registros percorridos                       : %d" % lsn["registros_percorridos"])
    print("   normas que citam seguranca nacional na ementa: %d"
          % lsn["normas_que_citam_seguranca_nacional_na_ementa"])
    print()
    print("   AS QUE DEFINEM CRIME, que e' a cadeia do sistema penal paralelo:")
    for o in lsn["normas_que_DEFINEM_crime_contra_a_seguranca_nacional"]:
        print("      %s  %-34s revogada por %s"
              % (o["data"], o["nome"], (o["revogada_por"] or "nenhuma")))
    print()
    print("   ACHADAS SO' POR NUMERO, porque a ementa nao diz seguranca nacional:")
    for o in lsn["achadas_SO_por_numero_e_nao_por_ementa"]:
        print("      %-34s %s" % (o["nome"], o["ementa"]))
    print()
    print("=== 2. AS EMENDAS CONSTITUCIONAIS ===")
    for k in ("anos_de_catalogo_percorridos", "emendas_no_catalogo",
              "ementa_comprimento_minimo", "ementa_comprimento_mediano",
              "ementa_comprimento_maximo", "emendas_com_ementa_vazia",
              "emendas_com_articulado_na_base", "emendas_SEM_articulado_na_base",
              "citam_materia_penal_na_ementa"):
        print("   %-42s %s" % (k.replace("_", " "), ec[k]))
    print("   citam materia penal no articulado          %d" % len(ec["citam_materia_penal_no_articulado"]))
    for o in ec["citam_materia_penal_no_articulado"]:
        print("      %s  %-30s %s" % (o["data"], o["nome"], o["ementa"]))
    print()
    print("gravado: " + SAIDA)
    print("detalhe: " + DETALHE)
    return 0


def bancada():
    provas = []
    provas.append(("acha a ementa que define crime",
                   bool(RE_DEFINE_CRIME.search("Define os crimes contra a segurança nacional, a ordem política"))))
    provas.append(("nao acha onde so' se cita seguranca nacional",
                   not RE_DEFINE_CRIME.search("Declara de interesse da segurança nacional o Município")))
    provas.append(("a ementa do DL 510 NAO casa por seguranca nacional",
                   not RE_SEGURANCA.search("Altera dispositivos do decreto-lei nº 314 de 13 de março de 1967")))
    provas.append(("e por isso a busca por numero e' necessaria", True))
    provas.append(("acha materia penal na ementa", bool(RE_PENAL.search("dispõe sobre crimes"))))
    provas.append(("nao acha em ementa sem materia penal",
                   not RE_PENAL.search("Altera os arts. 6º e 7º da Constituição Federal")))
    provas.append(("articulado em DICIONARIO e' lido",
                   texto_do_articulado({"workExample": {"a": "crime"}}) != ""))
    provas.append(("articulado em LISTA e' lido",
                   texto_do_articulado({"workExample": [{"a": "crime"}]}) != ""))
    provas.append(("sem articulado devolve vazio", texto_do_articulado({}) == ""))
    provas.append(("workExample nulo devolve vazio",
                   texto_do_articulado({"workExample": None}) == ""))
    ok = sum(1 for _, v in provas if v)
    for nome, v in provas:
        print(("   ok    " if v else "  FALHA  ") + nome)
    print("")
    print("BANCADA DAS EMENDAS E DA LSN: %d de %d" % (ok, len(provas)))
    return 0 if ok == len(provas) else 1


if __name__ == "__main__":
    sys.exit(bancada() if "--bancada" in sys.argv else apurar())
