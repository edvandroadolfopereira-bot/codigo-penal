# -*- coding: utf-8 -*-
# QUATRO ITENS DE ALCANCE, executaveis com o dado ja' no disco.
#
#   A. o PODER do teste da agenda, que o item 12 declara "ao alcance";
#   B. a SENSIBILIDADE da regua a variacao pequena, item 11;
#   C. o TETO EFETIVO com a causa de aumento aplicada, item 2;
#   D. o OBJETO de cada votacao nominal, item 15.
#
# Cada um traz o criterio LIDO DE LEI ou do proprio dado, e nunca criado aqui.

import collections
import csv
import io
import json
import os
import random
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

R = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(R, "BASE-CODIGO-PENAL.sqlite")
SEV = os.path.join(R, "cp-severidade-por-artigo.csv")
CAUSAS = os.path.join(R, "analise-cientifica", "causas-de-aumento.json")
MATERIA = os.path.join(R, "analise-cientifica", "materia-das-normas.json")
ROL = os.path.join(R, "analise-cientifica", "rol-hediondos.json")
SAIDA = os.path.join(R, "analise-cientifica", "pendencias-restantes.json")
# detalhe de cada votacao sem objeto na descricao, baixado da API da Camara por
# baixar_detalhe_votacoes_sem_objeto.py; e' a segunda passagem da classificacao
DETALHE = os.path.join(R, "analise-cientifica", "detalhe-votacoes-sem-objeto.json")

SEMENTE = 20260830
SORTEIOS_PODER = 2000
PERMUTACOES = 20000

# Cortes de gradacao fina, todos LIDOS DE LEI e nao criados aqui:
#   pena maxima ate' 2 anos       infracao de menor potencial ofensivo, Lei 9.099/1995, art. 61
#   pena minima ate' 1 ano        cabe suspensao condicional do processo, Lei 9.099/1995, art. 89
#   rol de crimes hediondos       Lei 8.072/1990
CORTE_MENOR_POTENCIAL_MESES = 24
CORTE_SURSIS_PROCESSUAL_MESES = 12


def ler_csv(p):
    with io.open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def num(v):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def qui(t):
    ln = list(t)
    if not ln:
        return 0.0
    nc = len(next(iter(t.values())))
    tot = sum(sum(t[l]) for l in ln)
    if not tot:
        return 0.0
    col = [sum(t[l][j] for l in ln) for j in range(nc)]
    x = 0.0
    for l in ln:
        for j in range(nc):
            esp = sum(t[l]) * col[j] / tot
            if esp > 0:
                x += (t[l][j] - esp) ** 2 / esp
    return x


def p_por_blocos(rot, col, nc, anos, n=PERMUTACOES, rnd=None):
    rnd = rnd or random.Random(SEMENTE)
    t = collections.defaultdict(lambda: [0] * nc)
    for a, b in zip(rot, col):
        t[a][b] += 1
    xobs = qui(t)
    r = list(rot)
    g = collections.defaultdict(list)
    for i, a in enumerate(anos):
        g[a // 10].append(i)
    grupos = [v for _, v in sorted(g.items())]
    ex = 0
    for _ in range(n):
        for gg in grupos:
            vs = [r[i] for i in gg]
            rnd.shuffle(vs)
            for i, v in zip(gg, vs):
                r[i] = v
        t2 = collections.defaultdict(lambda: [0] * nc)
        for a, b in zip(r, col):
            t2[a][b] += 1
        if qui(t2) >= xobs - 1e-12:
            ex += 1
    return (ex + 1) / (n + 1)


# ------------------------------------------------------------------ A. poder
def poder_do_teste_da_agenda():
    """Mede com que frequencia o teste da agenda detectaria associacao de tamanho dado.

    O desenho e' o mesmo do teste real: uma observacao por NORMA, permutacao em blocos
    de dez anos. O efeito e' construido trocando a materia de uma fracao das normas de
    ano eleitoral por uma materia unica, o que e' a forma mais favoravel a deteccao.
    Se nem assim o teste detecta, o poder e' baixo, e o nulo do trabalho e' ausencia de
    evidencia e nao evidencia de ausencia.
    """
    mt = json.load(io.open(MATERIA, encoding="utf-8"))
    linhas = []
    for mat, cc in mt["concentracao_por_materia"].items():
        linhas.append((mat, cc["eventos"]))
    # reconstroi a distribuicao por norma a partir do teste que vale
    tn = mt["teste_por_NORMA_que_vale"]
    n_normas = tn["normas"]
    n_elei = tn["normas_em_ano_eleitoral"]
    materias = sorted(mt["concentracao_por_materia"])
    pesos = [mt["concentracao_por_materia"][m]["normas"] for m in materias]
    total_peso = sum(pesos)
    rnd = random.Random(SEMENTE)
    anos_possiveis = list(range(1968, 2027))

    resultados = []
    for delta in (0.0, 0.2, 0.4, 0.6, 0.8):
        detectou = 0
        for _ in range(SORTEIOS_PODER):
            rot, col, anos = [], [], []
            for i in range(n_normas):
                elei = i < n_elei
                rot.append("eleitoral" if elei else "nao")
                anos.append(rnd.choice(anos_possiveis))
                if elei and rnd.random() < delta:
                    col.append(0)                     # materia unica, efeito plantado
                else:
                    col.append(rnd.choices(range(len(materias)), weights=pesos)[0])
            p = p_por_blocos(rot, col, len(materias), anos, n=400, rnd=rnd)
            if p < 0.05:
                detectou += 1
        resultados.append({"fracao_trocada": delta,
                           "detectou": detectou, "sorteios": SORTEIOS_PODER,
                           "poder": round(detectou / SORTEIOS_PODER, 4)})
    return {"desenho": ("uma observacao por norma, permutacao em blocos de dez anos, efeito "
                        "plantado trocando a materia de uma fracao das normas de ano eleitoral"),
            "normas": n_normas, "normas_em_ano_eleitoral": n_elei,
            "sorteios_por_tamanho": SORTEIOS_PODER,
            "resultados": resultados}


# ------------------------------------------------------- B. sensibilidade fina
def sensibilidade_da_regua():
    """Testa se a regua separa faixas definidas por CORTES DE LEI, e nao por escolha.

    O teste de validade da secao 2.8 usou contraste grosso, hediondo contra nao
    hediondo, com diferenca mediana de vinte e um anos e meio. Ele afasta a hipotese de
    regua cega, e nao a de regua pouco fina.

    Os cortes usados aqui vem de lei: dois anos de pena maxima e' o limite da infracao
    de menor potencial ofensivo, e um ano de pena minima e' o limite da suspensao
    condicional do processo, ambos da Lei 9.099/1995. O terceiro e' o rol de hediondos.
    """
    sev = ler_csv(SEV)
    rol = set(x["artigo"] for x in json.load(io.open(ROL, encoding="utf-8"))["detalhe"])
    faixas = collections.defaultdict(list)
    for s in sev:
        if s["parte"] != "Parte Especial":
            continue
        teto = num(s["teto_hoje_meses"])
        piso = num(s["piso_hoje_meses"])
        var = num(s["variacao_do_teto_meses"])
        if teto is None or piso is None or var is None:
            continue
        art = s["artigo"]
        if art in rol:
            f = "4. no rol de crimes hediondos"
        elif teto <= CORTE_MENOR_POTENCIAL_MESES:
            f = "1. menor potencial ofensivo, teto ate' 2 anos"
        elif piso <= CORTE_SURSIS_PROCESSUAL_MESES:
            f = "2. admite suspensao condicional do processo, piso ate' 1 ano"
        else:
            f = "3. comum, fora dos dois beneficios"
        faixas[f].append(teto)
    ordenadas = sorted(faixas)
    medianas = {}
    for f in ordenadas:
        v = sorted(faixas[f])
        medianas[f] = {"n": len(v), "mediana_do_teto_meses": v[len(v) // 2],
                       "menor": v[0], "maior": v[-1]}
    # a regua e' fina se a mediana CRESCE da faixa 1 a 4
    seq = [medianas[f]["mediana_do_teto_meses"] for f in ordenadas]
    monotona = all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1))
    # e o contraste mais dificil e' entre as faixas 2 e 3, que sao vizinhas
    viz = [f for f in ordenadas if f.startswith("2.") or f.startswith("3.")]
    dif = None
    if len(viz) == 2:
        dif = medianas[viz[1]]["mediana_do_teto_meses"] - medianas[viz[0]]["mediana_do_teto_meses"]
    return {"cortes": {"menor_potencial_ofensivo_meses": CORTE_MENOR_POTENCIAL_MESES,
                       "suspensao_condicional_do_processo_meses": CORTE_SURSIS_PROCESSUAL_MESES,
                       "fonte_dos_cortes": "Lei n. 9.099/1995, arts. 61 e 89, e Lei n. 8.072/1990"},
            "faixas": medianas, "mediana_cresce_da_faixa_1_a_4": monotona,
            "diferenca_entre_as_duas_faixas_vizinhas_meses": dif}


# --------------------------------------------------------- C. teto efetivo
def teto_efetivo():
    """Recalcula o teto de cada artigo com a maior causa de aumento aplicada.

    O que se mede e' o LIMITE SUPERIOR do teto, e nao o teto de um caso concreto: a
    causa de aumento incide ou nao conforme o fato, e decidir isso exige o caso. O
    limite superior e' bem definido e basta para dimensionar o vies.
    """
    ca = json.load(io.open(CAUSAS, encoding="utf-8"))
    fator = {str(x["artigo"]): x["fator_maximo"] for x in ca["epocas"]["hoje"]["subestimacao_por_artigo"]}
    fator40 = {str(x["artigo"]): x["fator_maximo"] for x in ca["epocas"]["1940"]["subestimacao_por_artigo"]}
    sev = ler_csv(SEV)
    tocados = []
    soma_med = soma_efe = 0.0
    for s in sev:
        if s["parte"] != "Parte Especial":
            continue
        teto = num(s["teto_hoje_meses"])
        if teto is None or teto <= 0:
            continue
        f = fator.get(s["artigo"], 1.0)
        soma_med += teto
        soma_efe += teto * f
        if f > 1.0:
            tocados.append({"artigo": s["artigo"], "teto_medido_meses": teto,
                            "fator": f, "teto_efetivo_meses": round(teto * f, 2)})
    return {"o_que_e": "limite superior do teto, com a maior causa de aumento do artigo aplicada",
            "artigos_com_causa_hoje": len(fator), "artigos_com_causa_em_1940": len(fator40),
            "dispositivos_recalculados": len(tocados),
            "artigos_distintos_recalculados": len(set(x["artigo"] for x in tocados)),
            "soma_dos_tetos_medidos_meses": round(soma_med, 2),
            "soma_dos_tetos_efetivos_meses": round(soma_efe, 2),
            "subestimacao_percentual": round(100.0 * (soma_efe - soma_med) / soma_med, 2) if soma_med else None,
            "detalhe": sorted(tocados, key=lambda x: -x["teto_efetivo_meses"])}


# --------------------------------------------------- D. objeto de cada votacao
OBJETO = [
    # Corrigido em 22/09/2026, lendo as 10 votacoes afetadas uma a uma. "Aprovado o Substitutivo
    # [...], ressalvados os destaques" e' a votacao do TEXTO-BASE, a principal da lei, e caia em
    # "destaque" porque essa entrada vinha antes; eram 8, entre elas a da Lei 13.964/2019 (408 a 9).
    # E "Proposta do Senado para que possa tramitar [...] rejeicao de materia identica" (art. 67 da
    # Constituicao) e' autorizacao processual, e saia como texto principal.
    ("autorizacao de tramitacao", r"possa tramitar|mat[ée]ria id[êe]ntica"),
    ("texto principal", r"aprovad[oa] (o|a) (substitutivo|subemenda substitutiva)"),
    ("emenda", r"rejeitadas as emendas do senado|aprovadas as emendas do senado"),
    # "REQ" e' a sigla que a Camara grava na alteracao de regime de tramitacao; sem ela,
    # medido em 22/09/2026, 12 votacoes ficavam sem objeto tendo o requerimento escrito
    ("requerimento", r"requerimento|\breq\b|urg[êe]ncia|inclus[ãa]o na ordem do dia|adiamento|retirada de pauta"),
    # As duas formas de destaque vao na MESMA entrada. Ter duas com o mesmo nome nao
    # muda a classificacao, porque o laco pega a primeira que casa, mas esconde a
    # primeira de qualquer leitura por dicionario. Foi a bancada que pegou isso.
    ("destaque", r"destaque|dvs\b|vota[çc][ãa]o em separado|mantido o texto|suprimido o texto|prefer[êe]ncia"),
    ("emenda", r"\bemenda|subemenda"),
    ("redacao final", r"reda[çc][ãa]o final"),
    ("substitutivo", r"substitutivo"),
    ("veto", r"\bveto\b"),
    ("texto principal", r"proposi[çc][ãa]o principal|mat[ée]ria|proje?to de lei|texto[- ]base|em globo"),
    ("parecer", r"\bparecer(es)?\b"),
]


def objeto_pelo_detalhe(det):
    """Segunda passagem: o objeto lido do detalhe da Camara, campo da ultima proposicao
    apresentada. So' classifica quando ele e' um requerimento; o resto fica sem objeto."""
    up = (det or {}).get("ultima_proposicao") or ""
    # sem a ultima proposicao, vale o campo de objetos possiveis quando TODOS sao requerimento
    # (medido: 121 das 126 votacoes tinham so' REQ ali; a 37896-1 nao tem ultima proposicao)
    obj = (det or {}).get("objetos_possiveis") or []
    if not up and obj and all(x.split()[0] == "REQ" for x in obj):
        return "requerimento"
    return "requerimento" if re.match(r"apresenta[çc][ãa]o d[oa] (requerimento|req)\b", up, re.I) else None


def objeto_das_votacoes():
    """Classifica cada votacao nominal pelo objeto, lido da descricao que a Camara grava.

    Isto responde a ressalva da secao da autoria: o percentual de sim cobre TODA votacao
    daquelas normas, inclusive processual, e sim ali nao equivale a sim ao agravamento.
    """
    c = sqlite3.connect(BASE)
    c.row_factory = sqlite3.Row
    vot = [dict(r) for r in c.execute(
        "SELECT norma, id_votacao, descricao, qtd_votos_nominais FROM camara_votacoes")]
    detalhe = {}
    if os.path.exists(DETALHE):
        detalhe = {str(x["id"]): x for x in json.load(io.open(DETALHE, encoding="utf-8"))["votacoes"]}
    por_id, passagem = {}, collections.Counter()
    for v in vot:
        d = (v["descricao"] or "").lower()
        achou = []
        for nome, padrao in OBJETO:
            if re.search(padrao, d, re.I):
                achou.append(nome)
        i = str(v["id_votacao"])
        if achou:
            por_id[i] = achou[0]; passagem["pela descricao"] += 1
        elif i not in detalhe:
            por_id[i] = "resultado sem objeto declarado"; passagem["sem detalhe lido"] += 1
        elif objeto_pelo_detalhe(detalhe[i]):
            por_id[i] = objeto_pelo_detalhe(detalhe[i]); passagem["pelo detalhe da Camara"] += 1
        else:
            por_id[i] = "resultado sem objeto declarado"; passagem["detalhe sem requerimento"] += 1
    cont = collections.Counter(por_id.values())
    votos = collections.Counter()
    sim = collections.Counter()
    nao = collections.Counter()
    for r in c.execute("SELECT id_votacao, voto, COUNT(*) n FROM camara_votos_nominais GROUP BY id_votacao, voto"):
        o = por_id.get(str(r["id_votacao"]), "sem votacao correspondente")
        votos[o] += r["n"]
        if r["voto"] == "Sim":
            sim[o] += r["n"]
        elif r["voto"] == "Não":
            nao[o] += r["n"]
    c.close()
    linhas = []
    # toda classe entra, inclusive a que nao tem voto nominal registrado: antes a tabela
    # iterava so' sobre os votos, e 2 votacoes de classe sem voto sumiam da soma
    for o in sorted(set(votos) | set(cont), key=lambda x: (-votos[x], -cont.get(x, 0))):
        val = sim[o] + nao[o]
        linhas.append({"objeto": o, "votacoes": cont.get(o, 0), "votos": votos[o],
                       "sim": sim[o], "nao": nao[o],
                       "pct_sim_entre_validos": round(100.0 * sim[o] / val, 1) if val else None})
    return {"criterio": ("palavra do objeto, lida da descricao que a Camara grava em cada "
                         "votacao; o que ela nao declara e' lido no detalhe da propria Camara, "
                         "campo da ultima proposicao apresentada, e so' conta quando e' requerimento"),
            "classificadas_por_passagem": dict(passagem),
            "limite_da_fonte": ("o campo da Camara mistura OBJETO e RESULTADO: parte das "
                                "descricoes diz apenas 'Aprovado', sem dizer o que foi "
                                "aprovado. Essas saem como resultado sem objeto declarado, e "
                                "nao forcadas para uma classe"),
            "votacoes_classificadas": sum(cont.values()),
            "sem_objeto_declarado": cont.get("resultado sem objeto declarado", 0),
            "por_objeto": linhas}


def apurar():
    for p in (BASE, SEV, CAUSAS, MATERIA, ROL):
        if not os.path.exists(p):
            print("FALHA REAL: falta " + p)
            return 1
    # a simulacao de poder e' cara, e por isso pode ser reaproveitada quando so' se
    # quer refazer as demais medidas. Reaproveitar so' e' licito se o resultado ja'
    # estiver gravado por uma execucao anterior DESTE mesmo script.
    reaproveita = "--sem-poder" in sys.argv and os.path.exists(SAIDA)
    if reaproveita:
        anterior = json.load(io.open(SAIDA, encoding="utf-8"))
        poder = anterior["A_poder_do_teste_da_agenda"]
        print("AVISO: a simulacao de poder foi REAPROVEITADA da execucao anterior.")
    else:
        poder = poder_do_teste_da_agenda()
    res = {"gerado_por": "apurar_pendencias_restantes.py",
           "A_poder_do_teste_da_agenda": poder,
           "B_sensibilidade_da_regua": sensibilidade_da_regua(),
           "C_teto_efetivo": teto_efetivo(),
           "D_objeto_das_votacoes": objeto_das_votacoes()}
    io.open(SAIDA, "w", encoding="utf-8", newline="").write(json.dumps(res, ensure_ascii=False, indent=1))

    a = res["A_poder_do_teste_da_agenda"]
    print("=== A. PODER DO TESTE DA AGENDA ===")
    print("   %d normas, %d em ano eleitoral, %d sorteios por tamanho de efeito"
          % (a["normas"], a["normas_em_ano_eleitoral"], a["sorteios_por_tamanho"]))
    print("   %-24s %10s" % ("fracao de normas trocada", "poder"))
    for x in a["resultados"]:
        print("   %-24s %9.1f%%" % ("%.0f%%" % (100 * x["fracao_trocada"]), 100 * x["poder"]))
    print()
    b = res["B_sensibilidade_da_regua"]
    print("=== B. SENSIBILIDADE DA REGUA, por cortes de lei ===")
    print("   %-56s %5s %10s" % ("faixa", "n", "mediana"))
    for f in sorted(b["faixas"]):
        d = b["faixas"][f]
        print("   %-56s %5d %10s" % (f, d["n"], d["mediana_do_teto_meses"]))
    print("   a mediana cresce da faixa 1 a 4: %s" % b["mediana_cresce_da_faixa_1_a_4"])
    print("   diferenca entre as duas faixas vizinhas: %s meses"
          % b["diferenca_entre_as_duas_faixas_vizinhas_meses"])
    print()
    cc = res["C_teto_efetivo"]
    print("=== C. TETO EFETIVO, com a causa de aumento aplicada ===")
    print("   artigos com causa hoje: %d | em 1940: %d" % (cc["artigos_com_causa_hoje"], cc["artigos_com_causa_em_1940"]))
    print("   dispositivos recalculados: %d, em %d artigos distintos"
          % (cc["dispositivos_recalculados"], cc["artigos_distintos_recalculados"]))
    print("   soma dos tetos medidos : %s meses" % cc["soma_dos_tetos_medidos_meses"])
    print("   soma dos tetos efetivos: %s meses" % cc["soma_dos_tetos_efetivos_meses"])
    print("   a regua subestima o total em %s%%" % cc["subestimacao_percentual"])
    print()
    dd = res["D_objeto_das_votacoes"]
    print("=== D. OBJETO DE CADA VOTACAO ===")
    print("   votacoes: %d | sem objeto declarado na fonte: %d"
          % (dd["votacoes_classificadas"], dd["sem_objeto_declarado"]))
    print("   por passagem: %s" % dd["classificadas_por_passagem"])
    print("   %-30s %10s %9s %9s" % ("objeto", "votacoes", "votos", "% sim"))
    for l in dd["por_objeto"]:
        print("   %-30s %10s %9d %8s%%" % (l["objeto"], l["votacoes"], l["votos"], l["pct_sim_entre_validos"]))
    print()
    print("gravado: " + SAIDA)
    return 0


def bancada():
    provas = []
    provas.append(("qui zero sem diferenca", abs(qui({"a": [10, 10], "b": [10, 10]})) < 1e-9))
    provas.append(("qui grande com separacao", qui({"a": [20, 0], "b": [0, 20]}) > 10))
    provas.append(("num le virgula decimal", num("12,5") == 12.5))
    provas.append(("num devolve None em texto", num("x") is None))
    for nome, padrao in OBJETO:
        pass
    provas.append(("classifica requerimento",
                   bool(re.search(dict(OBJETO)["requerimento"], "Requerimento de urgência", re.I))))
    provas.append(("classifica destaque",
                   bool(re.search(dict(OBJETO)["destaque"], "Destaque para votação em separado", re.I))))
    provas.append(("classifica emenda",
                   bool(re.search(dict(OBJETO)["emenda"], "Emenda de Plenário nº 3", re.I))))
    provas.append(("texto principal nao casa com requerimento",
                   not re.search(dict(OBJETO)["requerimento"], "Projeto de Lei nº 1234", re.I)))
    provas.append(("classifica parecer",
                   any(re.search(pd, "Aprovado o parecer.", re.I) for nm, pd in OBJETO if nm == "parecer")))
    provas.append(("mantido o texto e' destaque",
                   re.search(dict(OBJETO)["destaque"], "Mantido o texto. Sim: 300", re.I) is not None))
    provas.append(("nenhum nome de objeto aparece duas vezes na lista",
                   len(OBJETO) == len(set(nm for nm, _ in OBJETO))))
    provas.append(("a sigla REQ da alteracao de regime casa com requerimento",
                   bool(re.search(dict(OBJETO)["requerimento"], "em virtude da Aprovação do REQ 427/2021", re.I))))
    provas.append(("a sigla dentro de outra palavra nao casa",
                   not re.search(dict(OBJETO)["requerimento"], "requisito do tipo penal", re.I)))
    provas.append(("detalhe com requerimento classifica",
                   objeto_pelo_detalhe({"ultima_proposicao": "Apresentação do Requerimento de Audiência Pública n. 12/2019"}) == "requerimento"))
    provas.append(("detalhe com a sigla REQ classifica",
                   objeto_pelo_detalhe({"ultima_proposicao": "Apresentação do REQ n. 5/2021"}) == "requerimento"))
    provas.append(("detalhe com projeto de lei NAO classifica",
                   objeto_pelo_detalhe({"ultima_proposicao": "Apresentação do Projeto de Lei n. 10/2019"}) is None))
    provas.append(("sem ultima proposicao, objetos todos REQ classifica",
                   objeto_pelo_detalhe({"ultima_proposicao": None, "objetos_possiveis": ["REQ 13/2001"]}) == "requerimento"))
    provas.append(("sem ultima proposicao, objeto misto NAO classifica",
                   objeto_pelo_detalhe({"ultima_proposicao": None, "objetos_possiveis": ["REQ 1/2001", "PL 2/2001"]}) is None))
    provas.append(("sem detalhe a segunda passagem devolve nada",
                   objeto_pelo_detalhe({}) is None and objeto_pelo_detalhe(None) is None))
    provas.append(("'Aprovado' puro NAO casa com nada",
                   not any(re.search(pd, "Aprovado.", re.I) for nm, pd in OBJETO)))
    # o poder de um teste sob H0 tem que ficar proximo do nivel de significancia
    rnd = random.Random(1)
    rot = ["a"] * 20 + ["b"] * 20
    col = [rnd.randint(0, 3) for _ in range(40)]
    anos = [1990 + i // 4 for i in range(40)]
    p0 = p_por_blocos(rot, col, 4, anos, n=300, rnd=rnd)
    provas.append(("sob rotulo aleatorio o p nao e' pequeno por construcao", p0 > 0.01))
    # e com separacao total tem que ser pequeno
    col2 = [0] * 20 + [1] * 20
    p1 = p_por_blocos(rot, col2, 2, [1990] * 40, n=300, rnd=rnd)
    provas.append(("com separacao total dentro de um bloco o p e' pequeno", p1 < 0.05))
    ok = sum(1 for _, v in provas if v)
    for nome, v in provas:
        print(("   ok    " if v else "  FALHA  ") + nome)
    print("")
    print("BANCADA DAS PENDENCIAS RESTANTES: %d de %d" % (ok, len(provas)))
    return 0 if ok == len(provas) else 1


if __name__ == "__main__":
    sys.exit(bancada() if "--bancada" in sys.argv else apurar())
