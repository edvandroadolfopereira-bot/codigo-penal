# -*- coding: utf-8 -*-
"""Mede a posicao do individuo diante da lei penal, nas duas pontas.

POR QUE ESTA APURACAO EXISTE: o trabalho e' apresentado na disciplina Projeto de
Extensao III, Protecao de Individuos em Situacao Especial, e o usuario esclareceu em
30/08/2026 que "individuo" ali se le' como TODA pessoa, e nao como grupo nomeado.

Sob essa leitura o objeto nao e' um grupo, e' a POSICAO JURIDICA de quem esta' sob o
alcance da lei penal, nas duas pontas: como pessoa que a lei diz proteger, e como
pessoa que ela alcanca. O Codigo tem uma parte para cada uma, e a apuracao ja' feita
mede as duas.

DUAS MEDIDAS, e a segunda derruba o que a primeira parecia sustentar:

  A. AS DUAS PONTAS. A Parte Geral e' o regime juridico de quem responde ao processo
     e cumpre pena; a Parte Especial define o que o alcanca. Elas andam em direcoes
     opostas, e isso ja' esta' medido.

  B. O RECORTE ESTREITO, e a ressalva. Os tres Titulos que protegem pessoa em
     vulnerabilidade nomeada endurecem 10,1 pontos percentuais acima do resto do
     Codigo. TESTADO, a diferenca NAO se distingue do acaso: com 38 eventos, uma
     diferenca desse tamanho aparece sozinha em 21% das vezes. O que sobrevive e' a
     COMPOSICAO, e nao o contraste, e e' assim que ela vai para o texto.

O criterio do recorte e' do CODIGO, e nao meu: sao os Titulos I, VI e VII da Parte
Especial, na disposicao do legislador de 1940.
"""

import io
import json
import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")

R = os.path.dirname(os.path.abspath(__file__))
MATERIA = os.path.join(R, "analise-cientifica", "materia-das-normas.json")
PARTE_GERAL = os.path.join(R, "analise-cientifica", "severidade-parte-geral.json")
SAIDA = os.path.join(R, "analise-cientifica", "posicao-do-individuo.json")

RECORTE = ["DOS CRIMES CONTRA A PESSOA",
           "DOS CRIMES CONTRA A DIGNIDADE SEXUAL",
           "DOS CRIMES CONTRA A FAMÍLIA"]

PERMUTACOES = 200000
SEMENTE = 20260830


def _parte_geral(pg):
    """Le a contagem da Parte Geral nas DUAS leituras que a apuracao declara.

    ERRO MEU, medido em 30/08/2026: li `pg.get("abranda")` e recebi None, porque a
    chave mora em `contagem_por_direcao`. Pior, o script GRAVOU o None em vez de
    recusar, e eu quase corrigi o texto do trabalho, que estava certo.

    E ele esta' certo de forma mais cuidadosa do que a minha leitura: tres dos
    dezesseis institutos nao tem contraparte em 1940, porque foram CRIADOS ou
    EXTINTOS depois, e o trabalho conta as duas leituras lado a lado em vez de
    escolher uma em silencio.
    """
    c = pg.get("contagem_por_direcao")
    if not isinstance(c, dict):
        raise KeyError("a chave `contagem_por_direcao` nao esta na apuracao da Parte "
                       "Geral. Ausencia de medicao nunca sai como zero nem como None.")
    criados = c.get("instituto CRIADO depois de 1940", 0)
    extintos = c.get("instituto EXTINTO depois de 1940", 0)
    estrito_ab, estrito_ag = c.get("abranda", 0), c.get("agrava", 0)
    for k, v in (("abranda", estrito_ab), ("agrava", estrito_ag),
                 ("mantem", c.get("mantem", 0))):
        if not isinstance(v, int):
            raise KeyError("a direcao %r nao veio como numero: %r" % (k, v))
    return {
        "o_que_e": "o regime juridico de quem responde ao processo e cumpre pena",
        "institutos_pareados": pg.get("institutos_medidos", len(pg.get("institutos", []))),
        "por_subtracao_estrita": {
            "abranda": estrito_ab, "agrava": estrito_ag, "mantem": c.get("mantem", 0),
            "instituto_criado_depois_de_1940": criados,
            "instituto_extinto_depois_de_1940": extintos,
            "o_que_e": "conta so' o que tem parametro numerico nas duas epocas",
        },
        "com_as_tres_leituras_declaradas": {
            "abranda": estrito_ab + 2, "agrava": estrito_ag + 1,
            "mantem": c.get("mantem", 0),
            "o_que_e": "os tres institutos sem contraparte em 1940 entram pela leitura "
                       "que o Quadro 9 declara ao lado de cada um: o periodo depurador "
                       "da reincidencia e a extincao do prazo agravado da reabilitacao "
                       "abrandam, e o teto especial do crime continuado agrava",
        },
        "por_que_duas_contagens": "tres dos dezesseis institutos nao tem contraparte "
                                  "em 1940. Declarar as duas leituras e' mais honesto "
                                  "que escolher uma em silencio",
    }


def endurece(dic):
    """Endurecer e' agravar pena existente OU criar pena onde nao havia."""
    return dic.get("agrava", 0) + dic.get("cria pena", 0)


def total(dic):
    return endurece(dic) + dic.get("abranda", 0) + dic.get("mantem", 0)


def teste_de_permutacao(n_dentro, n_fora, end_dentro, end_fora, permutacoes, semente):
    """Permutacao simples: a pergunta nao tem tendencia temporal a preservar.

    Aqui NAO cabe permutacao por blocos, e a razao e' de desenho: o que se embaralha
    e' a MATERIA do evento, nao o ano dele, e materia nao tem tendencia no tempo que
    o embaralhamento simples destrua. Onde o ano entra na pergunta, como no teste do
    ciclo eleitoral, a permutacao continua sendo por blocos de dez anos.
    """
    rnd = random.Random(semente)
    n = n_dentro + n_fora
    eventos = [1] * (end_dentro + end_fora) + [0] * (n - end_dentro - end_fora)
    obs = end_dentro / n_dentro - end_fora / n_fora
    extremas = 0
    for _ in range(permutacoes):
        rnd.shuffle(eventos)
        d = sum(eventos[:n_dentro]) / n_dentro - sum(eventos[n_dentro:]) / n_fora
        if abs(d) >= abs(obs) - 1e-12:
            extremas += 1
    return obs, (extremas + 1) / (permutacoes + 1)


def apurar():
    em = json.load(io.open(MATERIA, encoding="utf-8"))["eventos_por_materia"]

    por_titulo = []
    d_end = d_tot = 0
    for k in RECORTE:
        if k not in em:
            print("FALHA REAL: o Titulo %r nao esta na classificacao." % k)
            return 1
        e, t = endurece(em[k]), total(em[k])
        d_end += e
        d_tot += t
        por_titulo.append({"titulo": k, "endurece": e,
                           "abranda": em[k].get("abranda", 0),
                           "mantem": em[k].get("mantem", 0),
                           "eventos": t,
                           "pct_endurece": round(100.0 * e / t, 1)})

    g_end = sum(endurece(v) for v in em.values())
    g_tot = sum(total(v) for v in em.values())
    f_end, f_tot = g_end - d_end, g_tot - d_tot

    obs, p = teste_de_permutacao(d_tot, f_tot, d_end, f_end, PERMUTACOES, SEMENTE)

    pg = json.load(io.open(PARTE_GERAL, encoding="utf-8"))

    fora = {
        "gerado_por": "apurar_posicao_do_individuo.py",
        "o_que_mede": "a posicao do individuo diante da lei penal, nas duas pontas: "
                      "como pessoa que a lei diz proteger, e como pessoa que ela alcanca",
        "o_que_nao_mede": "se a protecao produziu efeito, que exigiria serie de "
                          "vitimizacao por tipo penal, ausente deste acervo",
        "criterio_do_recorte": "os Titulos I, VI e VII da Parte Especial, na disposicao "
                               "do legislador de 1940. O criterio e' do Codigo, e nao "
                               "do autor",
        "A_as_duas_pontas": {
            "parte_geral": _parte_geral(pg),
            "parte_especial": {
                "o_que_e": "o que alcanca essa pessoa: os tipos penais e as penas",
                "eventos_datados": g_tot,
                "endurece": g_end,
                "pct_endurece": round(100.0 * g_end / g_tot, 1),
            },
        },
        "B_recorte_estreito": {
            "por_titulo": por_titulo,
            "soma_do_recorte": {"endurece": d_end, "eventos": d_tot,
                                "pct_endurece": round(100.0 * d_end / d_tot, 1)},
            "fora_do_recorte": {"endurece": f_end, "eventos": f_tot,
                                "pct_endurece": round(100.0 * f_end / f_tot, 1)},
            "participacao_do_recorte_no_total":
                round(100.0 * d_tot / g_tot, 1),
            "diferenca_em_pontos_percentuais": round(100.0 * obs, 1),
            "teste": {
                "pergunta": "a diferenca entre o recorte e o resto se distingue do acaso?",
                "metodo": "permutacao simples do rotulo de materia",
                "permutacoes": PERMUTACOES,
                "semente": SEMENTE,
                "p_bilateral": round(p, 4),
                "veredito": ("a diferenca NAO se distingue do acaso ao nivel de 5%"
                             if p >= 0.05 else
                             "a diferenca se distingue do acaso ao nivel de 5%"),
                "o_que_sobrevive": "a COMPOSICAO: %d dos %d eventos do recorte "
                                   "endurecem, e %d abrandam"
                                   % (d_end, d_tot,
                                      sum(x["abranda"] for x in por_titulo)),
            },
        },
    }
    io.open(SAIDA, "w", encoding="utf-8", newline="").write(
        json.dumps(fora, ensure_ascii=False, indent=1))

    print("=== A. AS DUAS PONTAS ===")
    a = fora["A_as_duas_pontas"]
    _e = a["parte_geral"]["por_subtracao_estrita"]
    _l = a["parte_geral"]["com_as_tres_leituras_declaradas"]
    print("   Parte Geral, regime de quem responde, em DUAS leituras declaradas:")
    print("      por subtracao estrita : %d abranda, %d agrava, %d mantem"
          % (_e["abranda"], _e["agrava"], _e["mantem"]))
    print("      com as tres leituras  : %d abranda, %d agrava, %d mantem"
          % (_l["abranda"], _l["agrava"], _l["mantem"]))
    print("   Parte Especial, o que a alcanca     : %d de %d eventos endurecem, %.1f%%"
          % (a["parte_especial"]["endurece"], a["parte_especial"]["eventos_datados"],
             a["parte_especial"]["pct_endurece"]))
    print()
    print("=== B. O RECORTE ESTREITO ===")
    print("   %-46s %6s %6s %8s" % ("titulo", "endur", "event", "% endur"))
    for x in por_titulo:
        print("   %-46s %6d %6d %7.1f%%"
              % (x["titulo"], x["endurece"], x["eventos"], x["pct_endurece"]))
    b = fora["B_recorte_estreito"]
    print("   %-46s %6d %6d %7.1f%%" % ("SOMA DO RECORTE", d_end, d_tot,
                                        b["soma_do_recorte"]["pct_endurece"]))
    print("   %-46s %6d %6d %7.1f%%" % ("FORA DO RECORTE", f_end, f_tot,
                                        b["fora_do_recorte"]["pct_endurece"]))
    print()
    print("   diferenca: %.1f pontos percentuais" % b["diferenca_em_pontos_percentuais"])
    print("   p bilateral por permutacao: %.4f" % b["teste"]["p_bilateral"])
    print("   %s" % b["teste"]["veredito"])
    print("   o que sobrevive: %s" % b["teste"]["o_que_sobrevive"])
    print()
    print("gravado: " + SAIDA)
    return 0


def bancada():
    ok, falha = [], []

    def prova(nome, cond, det=""):
        (ok if cond else falha).append(nome)
        print("   %s %s%s" % ("ok   " if cond else "FALHA", nome,
                              ("  <- " + det) if (det and not cond) else ""))

    print("=== BANCADA DA POSICAO DO INDIVIDUO ===")
    print()
    print("-- o que conta como endurecer --")
    prova("agravar pena existente endurece", endurece({"agrava": 3}) == 3)
    prova("criar pena onde nao havia TAMBEM endurece",
          endurece({"cria pena": 4}) == 4)
    prova("os dois somam", endurece({"agrava": 3, "cria pena": 4}) == 7)
    prova("abrandar NAO endurece", endurece({"abranda": 5}) == 0)
    prova("manter NAO endurece", endurece({"mantem": 5}) == 0)
    prova("o total soma as quatro direcoes",
          total({"agrava": 1, "cria pena": 2, "abranda": 3, "mantem": 4}) == 10)

    print()
    print("-- o teste de permutacao --")
    o1, p1 = teste_de_permutacao(38, 92, 34, 73, 2000, 1)
    prova("a diferenca observada e' a que se mede",
          abs(o1 - (34 / 38 - 73 / 92)) < 1e-12, "%.6f" % o1)
    prova("p fica entre 0 e 1", 0 < p1 <= 1, "%.4f" % p1)
    o2, p2 = teste_de_permutacao(50, 50, 50, 0, 2000, 1)
    prova("separacao TOTAL devolve p minimo", p2 < 0.01, "%.4f" % p2)
    o3, p3 = teste_de_permutacao(50, 50, 25, 25, 2000, 1)
    prova("ausencia de diferenca devolve p alto", p3 > 0.5, "%.4f" % p3)
    prova("a mesma semente devolve o mesmo p",
          teste_de_permutacao(38, 92, 34, 73, 2000, 1)[1] == p1)

    print()
    print("-- as duas leituras da Parte Geral --")
    _pg = {"institutos_medidos": 16,
           "contagem_por_direcao": {"agrava": 2, "abranda": 5, "mantem": 6,
                                    "instituto CRIADO depois de 1940": 2,
                                    "instituto EXTINTO depois de 1940": 1}}
    _r = _parte_geral(_pg)
    prova("a leitura estrita da 5 abranda e 2 agrava",
          _r["por_subtracao_estrita"]["abranda"] == 5
          and _r["por_subtracao_estrita"]["agrava"] == 2)
    prova("com as tres leituras da 7 abranda e 3 agrava",
          _r["com_as_tres_leituras_declaradas"]["abranda"] == 7
          and _r["com_as_tres_leituras_declaradas"]["agrava"] == 3)
    prova("as duas leituras somam os mesmos 16 institutos",
          _r["por_subtracao_estrita"]["abranda"] + _r["por_subtracao_estrita"]["agrava"]
          + _r["por_subtracao_estrita"]["mantem"]
          + _r["por_subtracao_estrita"]["instituto_criado_depois_de_1940"]
          + _r["por_subtracao_estrita"]["instituto_extinto_depois_de_1940"] == 16
          and _r["com_as_tres_leituras_declaradas"]["abranda"]
          + _r["com_as_tres_leituras_declaradas"]["agrava"]
          + _r["com_as_tres_leituras_declaradas"]["mantem"] == 16)
    try:
        _parte_geral({"institutos_medidos": 16})
        prova("chave ausente e' RECUSADA, e nao gravada como None", False, "aceitou")
    except KeyError:
        prova("chave ausente e' RECUSADA, e nao gravada como None", True)

    print()
    print("-- o recorte, e o que ele NAO pode fazer --")
    prova("o recorte tem exatamente tres Titulos, e sao do Codigo",
          len(RECORTE) == 3 and all(x.startswith("DOS CRIMES CONTRA") for x in RECORTE))
    prova("nenhum Titulo da PARTE GERAL entra no recorte da Parte Especial",
          not any("PENA" in x or "CRIME" == x for x in RECORTE))

    print()
    print("-- desligar o instrumento, e exigir que o veredito MUDE --")
    # Com UMA permutacao so', o p degenera para 1,0 e nenhuma diferenca e' detectavel.
    _o, p_morto = teste_de_permutacao(50, 50, 50, 0, 1, 1)
    prova("com o teste reduzido a uma permutacao, a separacao total DEIXA de aparecer",
          p_morto > 0.4, "%.4f, e antes era %.4f" % (p_morto, p2))

    print()
    print("BANCADA DA POSICAO DO INDIVIDUO: %d de %d" % (len(ok), len(ok) + len(falha)))
    if falha:
        print("REPROVOU: " + ", ".join(falha))
    return 1 if falha else 0


if __name__ == "__main__":
    sys.exit(bancada() if "--bancada" in sys.argv else apurar())
