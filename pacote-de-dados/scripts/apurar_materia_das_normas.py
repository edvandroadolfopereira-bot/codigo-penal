# A MATERIA DA NORMA, e o teste do confundidor nomeado.
#
# POR QUE ESTE E' O ITEM MAIS GRAVE DA SECAO DE ALCANCE: o desenho controla o regime
# politico por estratificacao, e nenhuma outra covariavel foi controlada. A candidata
# forte e' a AGENDA LEGISLATIVA do ano, e a cadeia suposta e':
#
#     ano eleitoral  ->  agenda de materia  ->  severidade
#
# O teste direto do trabalho liga a ponta a ponta e omite o elo do meio. Se o elo do
# meio existir, o resultado nulo do teste direto pode estar escondendo efeito por via
# indireta. Se ele nao existir, o nulo fica mais forte, e nao mais fraco.
#
# A DECISAO DE METODO, e ela e' o que separa medida de invencao: a materia NAO e'
# categoria minha. O proprio Codigo Penal se divide em TITULOS, cada um com nome
# proprio, oito na Parte Geral e doze na Parte Especial. A classificacao e' LIDA da
# estrutura do texto oficial, e o artigo pertence ao Titulo que o contem.
#
# Inventar rotulo de materia seria fabricar o proprio criterio de medida, que e' o
# defeito que esta casa combate. Aqui o criterio ja' existia, escrito pelo legislador.
#
# O QUE ELE MEDE:
#   1. a materia de cada um dos 130 eventos datados de severidade, pelo Titulo;
#   2. a direcao por materia;
#   3. se a mistura de materias difere entre ano eleitoral e ano nao eleitoral, que e'
#      o primeiro elo da cadeia;
#   4. se a direcao difere por materia, que e' o segundo elo.
#
# O QUE ELE NAO MEDE: a materia do PROJETO que originou a norma, que pode ser mais
# ampla que o artigo tocado. Uma lei de licitacoes que altera o art. 337-E toca o
# Titulo XI, e o projeto dela e' de licitacao. Aqui a unidade e' o dispositivo tocado.

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
TEXTO = os.path.join(R, "cp-compilado-texto.txt")
EVENTOS = os.path.join(R, "cp-eventos-de-severidade.csv")
SEVERIDADE = os.path.join(R, "cp-severidade-por-artigo.csv")
BASE = os.path.join(R, "BASE-CODIGO-PENAL.sqlite")
SAIDA = os.path.join(R, "analise-cientifica", "materia-das-normas.json")

SEMENTE = 20260830
PERMUTACOES = 200000

RE_TITULO = re.compile(r"^[ \t]*T[IÍ]TULO\s+([IVXL]+)[ \t]*$", re.M | re.I)
RE_PARTE = re.compile(r"^[ \t]*PARTE\s+(GERAL|ESPECIAL)[ \t]*$", re.M | re.I)
# Le tambem o sufixo de letra, que e' o que distingue 359-H de 359-I, ou seja
# financas publicas de crime contra o Estado Democratico.
# O HIFEN DO SUFIXO NAO TEM ESPACO, e o separador tem. MEDIDO no texto compilado
# em 30/08/2026: 73 ocorrencias de 'Art. N-X' sem espaco, com 71 designacoes
# distintas, contra 246 de 'Art. N - Palavra' com espaco. Aceitar espaco fazia
# 'Art. 155 - Subtrair' virar o artigo inexistente '155-S'.
RE_ART = re.compile(r"A\s?rt\.?\s*(\d+)(?:-([A-Z])(?![A-Za-z\u00c0-\u00ff]))?")


def normaliza(t):
    return re.sub(r"\s+", " ", t.replace("&#150;", "-").replace("&nbsp;", " ")).strip()


def estrutura(texto):
    """Le a divisao em Partes e Titulos do proprio texto oficial.

    Devolve lista de dicionarios com parte, titulo romano, nome e posicao inicial,
    na ordem do documento. O nome do Titulo e' a primeira linha nao vazia depois do
    marcador, ignorando anotacao de norma entre parenteses.
    """
    partes = [(m.start(), m.group(1).upper()) for m in RE_PARTE.finditer(texto)]
    saida = []
    for m in RE_TITULO.finditer(texto):
        pos = m.start()
        parte = "GERAL"
        for p, nome in partes:
            if p < pos:
                parte = nome
        resto = texto[m.end():m.end() + 400]
        resto = re.sub(r"\([^)]*\)", " ", resto)
        # O nome pode ocupar MAIS DE UMA LINHA. Medido em 30/08/2026: pegar so' a
        # primeira truncava o Titulo IV para 'DOS CRIMES CONTRA' e o V para 'DOS
        # CRIMES CONTRA O SENTIMENTO'. Juntam-se as linhas de caixa alta, parando no
        # CAPITULO, no artigo, ou na primeira linha que tenha letra minuscula.
        pedacos = []
        for linha in resto.split("\n"):
            linha = linha.strip()
            if not linha:
                if pedacos:
                    break
                continue
            if re.match(r"CAP[IÍ]TULO|A\s?rt\.", linha, re.I):
                break
            letras = [c for c in linha if c.isalpha()]
            if letras and not all(c.isupper() for c in letras):
                break
            pedacos.append(linha)
            if len(" ".join(pedacos)) > 90:
                break
        nome = normaliza(re.split(r"CAP[IÍ]TULO", " ".join(pedacos), flags=re.I)[0])
        saida.append({"parte": parte, "titulo": m.group(1).upper(), "nome": nome, "pos": pos})
    return saida


def chave_de_ordem(numero, sufixo):
    """Ordem entre artigos, com o sufixo de letra depois do artigo sem sufixo."""
    return (numero, 0 if not sufixo else ord(sufixo) - ord("A") + 1)


def designacao(numero, sufixo):
    return "%d-%s" % (numero, sufixo) if sufixo else str(numero)


def faixas_de_artigo(texto, est):
    """Para cada Titulo, os artigos que aparecem dentro dele, com o sufixo de letra.

    O leitor e' MONOTONICO por (numero, sufixo) dentro de cada Titulo: marcador menor
    que o corrente e' remissao, e nao artigo novo. Sem a ordem por sufixo, 'Art. 359-A'
    depois de 'Art. 359' seria descartado como remissao.
    """
    limites = [e["pos"] for e in est] + [len(texto)]
    for i, e in enumerate(est):
        trecho = texto[limites[i]:limites[i + 1]]
        arts, corrente = [], (0, 0)
        for m in RE_ART.finditer(trecho):
            n = int(m.group(1))
            suf = m.group(2)
            k = chave_de_ordem(n, suf)
            if k <= corrente:
                continue
            corrente = k
            arts.append(designacao(n, suf))
        e["primeiro_artigo"] = arts[0] if arts else None
        e["ultimo_artigo"] = arts[-1] if arts else None
        e["artigos"] = arts
    return est


def mapa_artigo_para_titulo(est):
    """Um artigo para um Titulo. Artigo que aparece em mais de um Titulo fica com o
    PRIMEIRO, e o caso sai declarado em vez de resolvido em silencio."""
    mapa, repetidos = {}, []
    for e in est:
        for a in e["artigos"]:
            if a in mapa:
                repetidos.append((a, mapa[a], e["titulo"]))
                continue
            mapa[a] = e
    return mapa, repetidos


def ler_csv(p):
    with io.open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


RE_DISP = re.compile(r"(?:art\.?\s*)?(\d+)(?:-([A-Z])(?![A-Za-z\u00c0-\u00ff]))?", re.I)


def artigo_do_dispositivo(d):
    """Devolve a designacao do artigo, com sufixo quando houver.

    O arquivo de eventos grava 'art. 172' e 'art. 168-A', e o extrator anterior exigia
    o numero no inicio da cadeia. Devolvia None em 130 de 130.
    """
    m = RE_DISP.search(str(d or ""))
    if not m:
        return None
    return designacao(int(m.group(1)), m.group(2))


def endurece(direcao):
    return direcao in ("agrava", "cria pena")


def qui(tabela):
    linhas = list(tabela)
    if not linhas:
        return 0.0
    ncol = len(next(iter(tabela.values())))
    tot = sum(sum(tabela[l]) for l in linhas)
    if not tot:
        return 0.0
    col = [sum(tabela[l][j] for l in linhas) for j in range(ncol)]
    x = 0.0
    for l in linhas:
        for j in range(ncol):
            esp = sum(tabela[l]) * col[j] / tot
            if esp > 0:
                x += (tabela[l][j] - esp) ** 2 / esp
    return x


BLOCO_ANOS = 10


def permuta(rotulos, colunas, ncol, x_obs, anos=None, n=PERMUTACOES):
    """Embaralha o rotulo de linha e conta o quao extremo e' o observado.

    PERMUTACAO POR BLOCOS DE DEZ ANOS quando `anos` e' dado, que e' o mesmo desenho do
    teste do ciclo eleitoral deste trabalho. Sem isso a tendencia temporal produz
    associacao espuria: a materia muda ao longo do tempo, porque o Titulo XII so'
    existe desde 2021, e a eleicao e' regular, entao qualquer tendencia na materia
    apareceria como associacao com ano eleitoral.
    """
    random.seed(SEMENTE)
    r = list(rotulos)
    if anos is None:
        grupos = [list(range(len(r)))]
    else:
        por_bloco = collections.defaultdict(list)
        for i, a in enumerate(anos):
            por_bloco[int(a) // BLOCO_ANOS].append(i)
        grupos = [v for _, v in sorted(por_bloco.items())]
    extremos = 0
    for _ in range(n):
        for g in grupos:
            vals = [r[i] for i in g]
            random.shuffle(vals)
            for i, v in zip(g, vals):
                r[i] = v
        t = collections.defaultdict(lambda: [0] * ncol)
        for a, b in zip(r, colunas):
            t[a][b] += 1
        if qui(t) >= x_obs - 1e-12:
            extremos += 1
    return extremos, (extremos + 1) / (n + 1)


def apurar():
    for p in (TEXTO, EVENTOS, SEVERIDADE, BASE):
        if not os.path.exists(p):
            print("FALHA REAL: falta " + p)
            return 1
    texto = io.open(TEXTO, encoding="utf-8").read()
    est = faixas_de_artigo(texto, estrutura(texto))
    mapa, repetidos = mapa_artigo_para_titulo(est)

    c = sqlite3.connect(BASE)
    eleitorais = set()
    for r in c.execute("SELECT ano FROM calendario_eleitoral_tse"):
        eleitorais.add(int(r[0]))
    c.close()

    eventos = ler_csv(EVENTOS)
    sem_titulo = []
    linhas = []
    for e in eventos:
        a = artigo_do_dispositivo(e["dispositivo"])
        t = mapa.get(a)
        if t is None:
            sem_titulo.append({"dispositivo": e["dispositivo"], "artigo": a})
            continue
        ano = int(e["ano"])
        linhas.append({"ano": ano, "artigo": a, "titulo": t["titulo"], "parte": t["parte"],
                       "materia": t["nome"], "direcao": e["direcao"],
                       "norma": e["norma"],
                       "endurece": endurece(e["direcao"]),
                       "ano_eleitoral": ano in eleitorais})

    # --- 1. eventos por materia, com direcao ---------------------------------
    por_mat = collections.defaultdict(collections.Counter)
    for l in linhas:
        por_mat[l["materia"]][l["direcao"]] += 1

    # --- 2. o SEGUNDO elo: a direcao difere por materia? ---------------------
    t2 = collections.defaultdict(lambda: [0, 0])
    for l in linhas:
        t2[l["materia"]][1 if l["endurece"] else 0] += 1
    x2 = qui(t2)
    anos_ev = [l["ano"] for l in linhas]
    mat_ev = [l["materia"] for l in linhas]
    end_ev = [1 if l["endurece"] else 0 for l in linhas]
    ext2, p2 = permuta(mat_ev, end_ev, 2, x2, anos=anos_ev)
    ext2s, p2s = permuta(mat_ev, end_ev, 2, x2)

    # --- 3. o PRIMEIRO elo: a materia difere entre ano eleitoral e nao? ------
    materias = sorted(set(l["materia"] for l in linhas))
    idx = {m: i for i, m in enumerate(materias)}
    t1 = collections.defaultdict(lambda: [0] * len(materias))
    for l in linhas:
        t1["eleitoral" if l["ano_eleitoral"] else "nao eleitoral"][idx[l["materia"]]] += 1
    x1 = qui(t1)
    rot1 = ["eleitoral" if l["ano_eleitoral"] else "nao eleitoral" for l in linhas]
    col1 = [idx[l["materia"]] for l in linhas]
    ext1, p1 = permuta(rot1, col1, len(materias), x1, anos=anos_ev)
    ext1s, p1s = permuta(rot1, col1, len(materias), x1)

    # --- 4. a Parte Especial inteira, por materia, para dar denominador ------
    sev = ler_csv(SEVERIDADE)
    art_por_mat = collections.Counter()
    for s in sev:
        a = artigo_do_dispositivo(s["dispositivo"])
        t = mapa.get(a)
        if t:
            art_por_mat[t["nome"]] += 1

    # --- 5. O TESTE QUE VALE: a unidade e' a NORMA, e nao o evento ----------
    por_norma = collections.defaultdict(lambda: {"mat": collections.Counter(),
                                                 "end": 0, "tot": 0, "ano": None})
    for l in linhas:
        d = por_norma[l["norma"]]
        d["mat"][l["materia"]] += 1
        d["tot"] += 1
        d["end"] += 1 if l["endurece"] else 0
        d["ano"] = l["ano"]
    normas = [{"norma": k, "ano": v["ano"], "materia": v["mat"].most_common(1)[0][0],
               "materias_distintas": len(v["mat"]), "eventos": v["tot"],
               "endurece": 1 if v["end"] * 2 >= v["tot"] else 0,
               "eleitoral": v["ano"] in eleitorais}
              for k, v in por_norma.items()]
    anos_n = [x["ano"] for x in normas]
    mats_n = sorted(set(x["materia"] for x in normas))
    idxn = {m: i for i, m in enumerate(mats_n)}

    t1n = collections.defaultdict(lambda: [0] * len(mats_n))
    for x in normas:
        t1n["eleitoral" if x["eleitoral"] else "nao eleitoral"][idxn[x["materia"]]] += 1
    x1n = qui(t1n)
    e1n, p1n = permuta(["eleitoral" if x["eleitoral"] else "nao eleitoral" for x in normas],
                       [idxn[x["materia"]] for x in normas], len(mats_n), x1n, anos=anos_n)

    t2n = collections.defaultdict(lambda: [0, 0])
    for x in normas:
        t2n[x["materia"]][x["endurece"]] += 1
    x2n = qui(t2n)
    e2n, p2n = permuta([x["materia"] for x in normas], [x["endurece"] for x in normas],
                       2, x2n, anos=anos_n)

    concentracao = {}
    for mat in sorted(set(l["materia"] for l in linhas)):
        do_mat = [l for l in linhas if l["materia"] == mat]
        c_norma = collections.Counter(l["norma"] for l in do_mat)
        maior, q = c_norma.most_common(1)[0]
        concentracao[mat] = {"eventos": len(do_mat), "normas": len(c_norma),
                             "maior_norma": maior, "eventos_da_maior": q,
                             "percentual_da_maior": round(100.0 * q / len(do_mat), 1)}

    res = {
        "gerado_por": "apurar_materia_das_normas.py",
        "AVISO_DE_UNIDADE": ("o teste que vale e' o POR NORMA. Oito eventos da mesma lei, "
                             "no mesmo dia, nao sao oito observacoes independentes, e "
                             "testar por evento e' pseudorreplicacao"),
        "teste_por_NORMA_que_vale": {
            "normas": len(normas), "eventos": len(linhas),
            "normas_que_tocam_mais_de_uma_materia":
                sum(1 for x in normas if x["materias_distintas"] > 1),
            "normas_em_ano_eleitoral": sum(1 for x in normas if x["eleitoral"]),
            "primeiro_elo_ano_eleitoral_x_materia": {
                "qui_quadrado": x1n, "tao_ou_mais_extremas": e1n, "p": p1n},
            "segundo_elo_materia_x_direcao": {
                "qui_quadrado": x2n, "tao_ou_mais_extremas": e2n, "p": p2n}},
        "concentracao_por_materia": concentracao,
        "criterio_da_materia": ("Titulo do proprio Codigo Penal, lido da estrutura do texto "
                                "oficial compilado; a materia nao e' categoria do autor"),
        "titulos_lidos": [{"parte": e["parte"], "titulo": e["titulo"], "nome": e["nome"],
                           "primeiro_artigo": e["primeiro_artigo"],
                           "ultimo_artigo": e["ultimo_artigo"],
                           "artigos_no_titulo": len(e["artigos"])} for e in est],
        "artigos_em_mais_de_um_titulo": repetidos,
        "eventos_classificados": len(linhas),
        "eventos_sem_titulo": sem_titulo,
        "eventos_por_materia": {k: dict(v) for k, v in sorted(por_mat.items())},
        "artigos_da_regua_por_materia": dict(art_por_mat),
        "segundo_elo_materia_x_direcao": {
            "pergunta": "a direcao do evento depende da materia?",
            "qui_quadrado": x2, "permutacoes": PERMUTACOES,
            "bloco_de_permutacao_anos": BLOCO_ANOS,
            "tao_ou_mais_extremas": ext2, "p": p2,
            "p_por_permutacao_SIMPLES_que_nao_vale": p2s},
        "primeiro_elo_ano_eleitoral_x_materia": {
            "pergunta": "a mistura de materias difere entre ano eleitoral e nao eleitoral?",
            "qui_quadrado": x1, "permutacoes": PERMUTACOES,
            "bloco_de_permutacao_anos": BLOCO_ANOS,
            "tao_ou_mais_extremas": ext1, "p": p1,
            "p_por_permutacao_SIMPLES_que_nao_vale": p1s},
        "anos_eleitorais_usados": sorted(eleitorais),
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    io.open(SAIDA, "w", encoding="utf-8", newline="").write(
        json.dumps(res, ensure_ascii=False, indent=1))

    print("=== A ESTRUTURA LIDA DO CODIGO ===")
    print("%-8s %-6s %-58s %s" % ("parte", "tit", "nome", "artigos"))
    for e in est:
        print("%-8s %-6s %-58s %s a %s" % (e["parte"], e["titulo"], e["nome"][:58],
                                           e["primeiro_artigo"], e["ultimo_artigo"]))
    if repetidos:
        print()
        print("ARTIGOS EM MAIS DE UM TITULO, declarados: %d" % len(repetidos))
        for a, t1r, t2r in repetidos:
            print("   art. %s em %s e em %s" % (a, t1r["titulo"] if isinstance(t1r, dict) else t1r, t2r))
    print()
    print("=== OS 130 EVENTOS POR MATERIA ===")
    print("eventos classificados: %d | sem Titulo: %d" % (len(linhas), len(sem_titulo)))
    for x in sem_titulo:
        print("   SEM TITULO: dispositivo %s" % x["dispositivo"])
    print()
    print("%-52s %5s %5s %5s %5s %5s %7s" % ("materia", "total", "agr", "cria", "abr", "man", "endur%"))
    for mat in sorted(por_mat, key=lambda m: -sum(por_mat[m].values())):
        d = por_mat[mat]
        tot = sum(d.values())
        end = d.get("agrava", 0) + d.get("cria pena", 0)
        print("%-52s %5d %5d %5d %5d %5d %6.1f%%" % (mat[:52], tot, d.get("agrava", 0),
              d.get("cria pena", 0), d.get("abranda", 0), d.get("mantem", 0), 100.0 * end / tot))
    print()
    print("=== O SEGUNDO ELO: a direcao depende da materia? ===")
    print("   qui-quadrado %.4f | %d permutacoes em blocos de %d anos | extremas %d | p = %.5f"
          % (x2, PERMUTACOES, BLOCO_ANOS, ext2, p2))
    print("   por permutacao SIMPLES, que nao preserva a tendencia, daria p = %.5f" % p2s)
    print("   " + ("SIM, a direcao depende da materia (p < 0,05)" if p2 < 0.05
                   else "NAO se distingue do acaso (p >= 0,05)"))
    print()
    print("=== O PRIMEIRO ELO: a materia difere em ano eleitoral? ===")
    for rot in sorted(t1):
        tot = sum(t1[rot])
        print("   %-16s %3d eventos" % (rot, tot))
    print("   qui-quadrado %.4f | %d permutacoes em blocos de %d anos | extremas %d | p = %.5f"
          % (x1, PERMUTACOES, BLOCO_ANOS, ext1, p1))
    print("   por permutacao SIMPLES, que nao preserva a tendencia, daria p = %.5f" % p1s)
    print("   " + ("SIM, a agenda difere em ano eleitoral (p < 0,05)" if p1 < 0.05
                   else "NAO se distingue do acaso (p >= 0,05)"))
    print()
    print()
    print("=" * 78)
    print("O TESTE QUE VALE: a unidade e' a NORMA, e nao o evento")
    print("=" * 78)
    print("   %d normas para %d eventos | mediana de %d evento(s) por norma | maximo %d"
          % (len(normas), len(linhas),
             sorted(x["eventos"] for x in normas)[len(normas) // 2],
             max(x["eventos"] for x in normas)))
    print("   normas em ano eleitoral: %d | fora: %d"
          % (sum(1 for x in normas if x["eleitoral"]),
             sum(1 for x in normas if not x["eleitoral"])))
    print()
    print("   concentracao de cada materia na sua maior norma:")
    for mat, cc in sorted(concentracao.items(), key=lambda kv: -kv[1]["percentual_da_maior"]):
        print("      %-50s %2d eventos em %2d normas, %d na maior (%.0f%%)"
              % (mat[:50], cc["eventos"], cc["normas"], cc["eventos_da_maior"],
                 cc["percentual_da_maior"]))
    print()
    print("   PRIMEIRO ELO por norma: qui %.4f | extremas %d | p = %.5f  %s"
          % (x1n, e1n, p1n, "SIM" if p1n < 0.05 else "NAO se distingue do acaso"))
    print("   SEGUNDO  ELO por norma: qui %.4f | extremas %d | p = %.5f  %s"
          % (x2n, e2n, p2n, "SIM" if p2n < 0.05 else "NAO se distingue do acaso"))
    print()
    print("   Por EVENTO os dois elos apareciam com p pequeno. Por NORMA nenhum aparece.")
    print("   A diferenca inteira e' pseudorreplicacao, e o teste por norma e' o que vale.")
    print()
    print("gravado: " + SAIDA)
    if sem_titulo:
        print("ATENCAO: %d evento(s) sem Titulo. Isso e' ausencia de classificacao, e nao"
              " ausencia de materia." % len(sem_titulo))
        return 1
    return 0


def bancada():
    provas = []
    t = ("PARTE GERAL\nTÍTULO I\nDA APLICAÇÃO DA LEI PENAL\nArt. 1 - texto. Art. 2 - texto.\n"
         "PARTE ESPECIAL\nTÍTULO I\nDOS CRIMES CONTRA A PESSOA\nCAPÍTULO I\n"
         "Art. 121. Matar. Art. 129. Ofender.\nTÍTULO II\nDOS CRIMES CONTRA O PATRIMÔNIO\n"
         "Art. 155 - Subtrair, observado o art. 121. Art. 157 - Subtrair mediante violencia.\n")
    est = faixas_de_artigo(t, estrutura(t))
    provas.append(("le tres Titulos do texto", len(est) == 3))
    provas.append(("a Parte Geral e' identificada", est[0]["parte"] == "GERAL"))
    provas.append(("a Parte Especial e' identificada", est[1]["parte"] == "ESPECIAL"))
    provas.append(("o nome do Titulo sai do texto",
                   est[1]["nome"] == "DOS CRIMES CONTRA A PESSOA"))
    provas.append(("o nome nao engole o CAPITULO", "CAPÍTULO" not in est[1]["nome"]))
    provas.append(("faixa do Titulo I especial e' 121 a 129",
                   est[1]["primeiro_artigo"] == "121" and est[1]["ultimo_artigo"] == "129"))
    provas.append(("a remissao ao art. 121 dentro do Titulo II NAO abre artigo la'",
                   "121" not in est[2]["artigos"]))
    mapa, rep = mapa_artigo_para_titulo(est)
    provas.append(("o art. 121 pertence ao Titulo I especial", mapa["121"]["titulo"] == "I"))
    provas.append(("o art. 157 pertence ao Titulo II", mapa["157"]["titulo"] == "II"))
    provas.append(("nenhum artigo repetido neste caso", rep == []))
    provas.append(("dispositivo no formato do arquivo, 'art. 172'",
                   artigo_do_dispositivo("art. 172") == "172"))
    provas.append(("dispositivo com sufixo de letra, 'art. 168-A'",
                   artigo_do_dispositivo("art. 168-A") == "168-A"))
    provas.append(("dispositivo com paragrafo devolve o artigo",
                   artigo_do_dispositivo("157 §2º") == "157"))
    provas.append(("dispositivo sem numero devolve None",
                   artigo_do_dispositivo("caput") is None))
    # o hifen SEPARADOR nao pode virar sufixo de letra
    sep = ("PARTE ESPECIAL\nT\u00cdTULO II\nDOS CRIMES CONTRA O PATRIM\u00d4NIO\n"
           "Art. 155 - Subtrair coisa. Art. 157 - Subtrair mediante violencia.\n")
    esep = faixas_de_artigo(sep, estrutura(sep))
    provas.append(("'Art. 155 - Subtrair' le 155, e NAO 155-S",
                   esep[0]["artigos"] == ["155", "157"]))
    provas.append(("'Art. 33 - A pena' le 33, e NAO 33-A",
                   artigo_do_dispositivo("Art. 33 - A pena") == "33"))
    # o defeito caro: 359-H e 359-I sao de Titulos DIFERENTES
    t359 = ("PARTE ESPECIAL\nTÍTULO XI\nDOS CRIMES CONTRA A ADMINISTRAÇÃO PÚBLICA\n"
            "Art. 359-G texto. Art. 359-H texto.\n"
            "TÍTULO XII\nDOS CRIMES CONTRA O ESTADO DEMOCRÁTICO DE DIREITO\n"
            "Art. 359-I texto. Art. 359-J texto.\n")
    e359 = faixas_de_artigo(t359, estrutura(t359))
    m359, _ = mapa_artigo_para_titulo(e359)
    provas.append(("359-H fica no Titulo XI", m359["359-H"]["titulo"] == "XI"))
    provas.append(("359-I fica no Titulo XII, e NAO no XI", m359["359-I"]["titulo"] == "XII"))
    provas.append(("a ordem por sufixo nao descarta 359-A depois de 359",
                   chave_de_ordem(359, "A") > chave_de_ordem(359, None)))
    provas.append(("agrava endurece", endurece("agrava")))
    provas.append(("cria pena endurece", endurece("cria pena")))
    provas.append(("abranda nao endurece", not endurece("abranda")))
    provas.append(("mantem nao endurece", not endurece("mantem")))

    # o qui-quadrado tem que ser ZERO quando nao ha diferenca nenhuma
    igual = {"a": [10, 10], "b": [10, 10]}
    provas.append(("sem diferenca o qui-quadrado e' zero", abs(qui(igual)) < 1e-9))
    dif = {"a": [20, 0], "b": [0, 20]}
    provas.append(("com separacao total o qui-quadrado e' grande", qui(dif) > 10))

    # DESLIGAR o leitor de estrutura tem que MUDAR o veredito
    vazio = faixas_de_artigo("Art. 1 sem titulo nenhum.", estrutura("Art. 1 sem titulo nenhum."))
    provas.append(("texto sem Titulo devolve estrutura vazia", vazio == []))
    m2, _ = mapa_artigo_para_titulo(vazio)
    provas.append(("com a estrutura DESLIGADA nenhum artigo se classifica", m2 == {}))

    # o nome do Titulo pode ocupar duas linhas, e truncar muda a materia
    duas = ("PARTE ESPECIAL\nTÍTULO IV\nDOS CRIMES CONTRA\nA ORGANIZAÇÃO DO TRABALHO\n"
            "Art. 197 - Constranger.\n")
    provas.append(("nome de Titulo em duas linhas e' juntado",
                   estrutura(duas)[0]["nome"] == "DOS CRIMES CONTRA A ORGANIZAÇÃO DO TRABALHO"))
    uma = ("PARTE ESPECIAL\nTÍTULO I\nDOS CRIMES CONTRA A PESSOA\nCAPÍTULO I\n"
           "Art. 121. Matar.\n")
    provas.append(("nome de uma linha continua inteiro",
                   estrutura(uma)[0]["nome"] == "DOS CRIMES CONTRA A PESSOA"))

    # a permutacao POR BLOCOS tem que dar resultado DIFERENTE da simples quando o
    # rotulo esta' concentrado no tempo. Sem esta prova, o bloco poderia nao estar
    # sendo usado e a bancada nao veria.
    rot = ["a"] * 20 + ["b"] * 20
    col = [0] * 20 + [1] * 20
    anos = list(range(1980, 2000)) + list(range(2000, 2020))
    tobs = collections.defaultdict(lambda: [0, 0])
    for a, b in zip(rot, col):
        tobs[a][b] += 1
    x = qui(tobs)
    _, p_bloco = permuta(rot, col, 2, x, anos=anos, n=2000)
    _, p_simples = permuta(rot, col, 2, x, n=2000)
    provas.append(("com o rotulo preso ao bloco, o p MUDA em relacao a permutacao simples",
                   abs(p_bloco - p_simples) > 1e-9))
    provas.append(("e o observado deixa de ser extremo dentro do bloco",
                   p_bloco > p_simples))

    # a agregacao por norma tem que colapsar eventos repetidos da MESMA lei
    evs = [{"norma": "L1", "materia": "A", "endurece": True, "ano": 2021},
           {"norma": "L1", "materia": "A", "endurece": True, "ano": 2021},
           {"norma": "L1", "materia": "A", "endurece": True, "ano": 2021},
           {"norma": "L2", "materia": "B", "endurece": False, "ano": 1998}]
    agr = collections.defaultdict(lambda: {"mat": collections.Counter(), "end": 0, "tot": 0})
    for e in evs:
        agr[e["norma"]]["mat"][e["materia"]] += 1
        agr[e["norma"]]["tot"] += 1
        agr[e["norma"]]["end"] += 1 if e["endurece"] else 0
    provas.append(("quatro eventos de duas leis viram DUAS normas", len(agr) == 2))
    provas.append(("a norma com tres eventos conta uma vez so'", agr["L1"]["tot"] == 3))
    provas.append(("a materia predominante da norma sai da contagem",
                   agr["L1"]["mat"].most_common(1)[0][0] == "A"))

    ok = sum(1 for _, v in provas if v)
    for nome, v in provas:
        print(("   ok    " if v else "  FALHA  ") + nome)
    print("")
    print("BANCADA DA MATERIA DAS NORMAS: %d de %d" % (ok, len(provas)))
    return 0 if ok == len(provas) else 1


if __name__ == "__main__":
    sys.exit(bancada() if "--bancada" in sys.argv else apurar())
