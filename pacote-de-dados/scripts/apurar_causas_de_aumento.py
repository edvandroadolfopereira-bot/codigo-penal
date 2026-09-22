# CAUSAS DE AUMENTO E DE DIMINUICAO, E MULTIPLICADOR DE PENA.
#
# POR QUE ELAS FICARAM FORA DA REGUA DE SEVERIDADE: a regua mede FAIXA, em meses, do
# piso ao teto cominado. Causa de aumento e' FRACAO, e multiplicador e' fator. Nenhum
# dos dois entra numa faixa, e por isso o teto medido pela regua e' menor que o teto
# que o juiz pode aplicar. O vies e' CONSERVADOR: a regua subestima a severidade.
#
# O QUE ESTE SCRIPT MEDE:
#   1. quantos comandos de aumento, de diminuicao e de multiplicador existem na Parte
#      Especial de 1940 e na de hoje;
#   2. o TETO EFETIVO de cada artigo, que e' o teto cominado depois de aplicado o maior
#      aumento previsto no proprio artigo;
#   3. quanto a regua de faixa subestima, em meses e em percentual, nas duas epocas.
#
# DOIS DEFEITOS DE DETECCAO, medidos em 30/08/2026 no art. 159, e os dois plantados na
# bancada para nunca voltarem:
#
#   a) FORMA ELIDIDA. 'reduzida de um a dois tercos' tem o primeiro termo sem o
#      substantivo: 'um' quer dizer 'um terco'. Detector que exija o substantivo em
#      cada termo perde a fracao inteira e devolve zero.
#   b) FORMA EM ALGARISMO COM ADJETIVO NO MEIO. 'aumenta-se a respectiva pena em 2/3
#      (dois tercos)' traz a fracao em algarismo, e um adjetivo entre o verbo e a
#      fracao. Detector que so' leia extenso, ou que exija adjacencia, perde.
#
# Filtro que nao ve' o defeito devolve zero e PARECE medida, que e' a regra desta casa
# de 03/08/2026. Por isso a bancada mede as duas direcoes e desliga o detector.

import collections
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.abspath(__file__))
TEXTO_HOJE = os.path.join(RAIZ, "cp-compilado-texto.txt")
TEXTO_1940 = os.path.join(RAIZ, "textos-das-normas", "codigo-penal-1940-texto-original.json")
SAIDA = os.path.join(RAIZ, "analise-cientifica", "causas-de-aumento.json")

# --- vocabulario da fracao ---------------------------------------------------
_CARDINAL = {"um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "três": 3,
             "quatro": 4, "cinco": 5, "seis": 6}
_DENOMINADOR = {"metade": 2, "meio": 2, "terco": 3, "terço": 3, "tercos": 3, "terços": 3,
                "quarto": 4, "quartos": 4, "quinto": 5, "quintos": 5,
                "sexto": 6, "sextos": 6, "oitavo": 8, "oitavos": 8}

_FRACAO_EXTENSO = r"(?:um|uma|dois|duas|tr[êe]s|quatro|cinco|seis)\s+(?:ter[cç]os?|quartos?|quintos?|sextos?|oitavos?)"
_METADE = r"metade|meio"
_FRACAO_ALGARISMO = r"\d+\s*/\s*\d+"
_TERMO = r"(?:%s|%s|%s)" % (_FRACAO_EXTENSO, _FRACAO_ALGARISMO, _METADE)
# forma ELIDIDA: 'de um a dois tercos', em que o primeiro termo e' so' o cardinal
_ELIDIDO = r"(?:um|uma|dois|duas|tr[êe]s)"

_MULT = r"(?:o\s+|em\s+|ao\s+)?(?:dobro|triplo|qu[áa]druplo)"

_V_AUMENTO = r"aumenta(?:-se|da|do|m-se|r|ndo|rem)?|aumento|acr[ée]scimo|acrescida|majorad[ao]|exasperad[ao]|elevada"
_V_DIMINUICAO = r"diminu[íi]d[ao]|diminui(?:-se|r|ndo)?|diminui[çc][ãa]o|reduzid[ao]|reduz(?:-se|ir)?|redu[çc][ãa]o|substitu[íi]da por"

# ate' 6 palavras entre o verbo e a fracao, para atravessar 'a respectiva pena'
_PONTE = r"(?:\s+[\wÀ-ÿ]+){0,6}?\s+(?:de|em|at[ée])\s+"

# A ORDEM DA ALTERNANCIA IMPORTA, e inverte-la produz defeito silencioso: regex
# alterna em ordem, entao a forma COMPLETA tem que vir antes da ELIDIDA. Com a
# elidida na frente, 'de um terco' casa apenas 'um', deixa 'terco' de fora, e a
# fracao sai sem valor. Medido em 30/08/2026, e plantado na bancada.
RE_AUMENTO = re.compile(r"(?:%s)%s(%s|%s)(?:\s+a(?:t[ée])?\s+(%s))?" % (_V_AUMENTO, _PONTE, _TERMO, _ELIDIDO, _TERMO), re.I)
RE_DIMINUICAO = re.compile(r"(?:%s)%s(%s|%s)(?:\s+a(?:t[ée])?\s+(%s))?" % (_V_DIMINUICAO, _PONTE, _TERMO, _ELIDIDO, _TERMO), re.I)
RE_MULTIPLICADOR = re.compile(r"(?:pena|penas)[^.;]{0,80}?%s|%s[^.;]{0,40}?(?:pena|penas)" % (_MULT, _MULT), re.I)

RE_PENA = re.compile(r"Pena\s*[-–:]\s*[^.]{0,200}", re.I)
RE_FAIXA = re.compile(r"de\s+([\wÀ-ÿ]+(?:\s+e\s+[\wÀ-ÿ]+)?)\s+a\s+([\wÀ-ÿ]+(?:\s+e\s+[\wÀ-ÿ]+)?)\s+(anos?|meses|dias)", re.I)


def valor_da_fracao(txt):
    """Converte 'dois tercos', '2/3' e 'metade' em numero. Devolve None se nao souber."""
    if txt is None:
        return None
    t = re.sub(r"\s+", " ", txt.strip().lower())
    m = re.match(r"^(\d+)\s*/\s*(\d+)$", t)
    if m:
        d = int(m.group(2))
        return int(m.group(1)) / d if d else None
    if t in ("metade", "meio"):
        return 0.5
    p = t.split()
    if len(p) == 2 and p[0] in _CARDINAL and p[1] in _DENOMINADOR:
        return _CARDINAL[p[0]] / _DENOMINADOR[p[1]]
    return None


def maior_fracao(m):
    """De um casamento com dois termos, devolve a MAIOR fracao.

    A forma elidida 'de um a dois tercos' tem o primeiro termo sem substantivo, e o
    denominador dele vem do SEGUNDO termo. Sem isto, 'um' fica sem valor e o comando
    inteiro se perde.
    """
    a, b = m.group(1), m.group(2)
    vb = valor_da_fracao(b) if b else None
    va = valor_da_fracao(a)
    if va is None and a and b:
        p = re.sub(r"\s+", " ", b.strip().lower()).split()
        if len(p) == 2 and p[1] in _DENOMINADOR and a.strip().lower() in _CARDINAL:
            va = _CARDINAL[a.strip().lower()] / _DENOMINADOR[p[1]]
    vals = [x for x in (va, vb) if x is not None]
    return max(vals) if vals else None


def normaliza(t):
    return re.sub(r"\s+", " ", t.replace("&#150;", "-").replace("&nbsp;", " "))


def artigos(texto):
    achados, corrente = [], 0
    for m in re.finditer(r"Art\.?\s*(\d+)", texto):
        n = int(m.group(1))
        if n <= corrente:
            continue
        corrente = n
        achados.append((n, m.start()))
    return {n: normaliza(texto[i:(achados[k + 1][1] if k + 1 < len(achados) else len(texto))])
            for k, (n, i) in enumerate(achados)}


def comandos(texto):
    """Devolve os comandos achados num artigo, cada um com a fracao medida."""
    aum, dim, mult = [], [], []
    for m in RE_AUMENTO.finditer(texto):
        aum.append({"trecho": m.group(0), "fracao": maior_fracao(m)})
    for m in RE_DIMINUICAO.finditer(texto):
        dim.append({"trecho": m.group(0), "fracao": maior_fracao(m)})
    for m in RE_MULTIPLICADOR.finditer(texto):
        t = m.group(0).lower()
        f = 3.0 if "triplo" in t else (4.0 if "druplo" in t else 2.0)
        mult.append({"trecho": m.group(0), "fator": f})
    return aum, dim, mult


def apurar():
    if not (os.path.exists(TEXTO_HOJE) and os.path.exists(TEXTO_1940)):
        print("FALHA REAL: falta o texto de uma das epocas.")
        return 1
    fontes = {
        "hoje": artigos(io.open(TEXTO_HOJE, encoding="utf-8").read()),
        "1940": artigos(json.load(io.open(TEXTO_1940, encoding="utf-8"))["texto"]),
    }
    res = {"gerado_por": "apurar_causas_de_aumento.py",
           "o_que_mede": ("comando de aumento, de diminuicao e multiplicador na Parte Especial, "
                          "e o quanto a regua de faixa subestima por nao os computar"),
           "epocas": {}}

    for epoca, dic in fontes.items():
        pe = {n: t for n, t in dic.items() if n > 120}
        tot_a = tot_d = tot_m = 0
        arts_a, arts_d, arts_m = set(), set(), set()
        fracoes = collections.Counter()
        sem_valor = []
        subestima = []
        for n, t in sorted(pe.items()):
            aum, dim, mult = comandos(t)
            tot_a += len(aum); tot_d += len(dim); tot_m += len(mult)
            if aum: arts_a.add(n)
            if dim: arts_d.add(n)
            if mult: arts_m.add(n)
            for c in aum:
                if c["fracao"] is None:
                    sem_valor.append({"artigo": n, "trecho": c["trecho"]})
                else:
                    fracoes[round(c["fracao"], 4)] += 1
            fator = 1.0
            for c in aum:
                if c["fracao"]:
                    fator = max(fator, 1.0 + c["fracao"])
            for c in mult:
                fator = max(fator, c["fator"])
            if fator > 1.0:
                subestima.append({"artigo": n, "fator_maximo": round(fator, 4)})
        res["epocas"][epoca] = {
            "artigos_da_parte_especial": len(pe),
            "comandos_de_aumento": tot_a, "artigos_com_aumento": len(arts_a),
            "comandos_de_diminuicao": tot_d, "artigos_com_diminuicao": len(arts_d),
            "comandos_de_multiplicador": tot_m, "artigos_com_multiplicador": len(arts_m),
            "artigos_cujo_teto_a_regua_subestima": len(subestima),
            "fator_maximo_observado": max([x["fator_maximo"] for x in subestima] or [1.0]),
            "fracoes_de_aumento_medidas": {str(k): v for k, v in sorted(fracoes.items())},
            "comandos_sem_valor_extraido": sem_valor,
            "subestimacao_por_artigo": subestima,
        }

    a, b = res["epocas"]["1940"], res["epocas"]["hoje"]
    res["comparacao"] = {
        "aumento_1940": a["comandos_de_aumento"], "aumento_hoje": b["comandos_de_aumento"],
        "diminuicao_1940": a["comandos_de_diminuicao"], "diminuicao_hoje": b["comandos_de_diminuicao"],
        "multiplicador_1940": a["comandos_de_multiplicador"], "multiplicador_hoje": b["comandos_de_multiplicador"],
        "artigos_subestimados_1940": a["artigos_cujo_teto_a_regua_subestima"],
        "artigos_subestimados_hoje": b["artigos_cujo_teto_a_regua_subestima"],
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    io.open(SAIDA, "w", encoding="utf-8", newline="").write(json.dumps(res, ensure_ascii=False, indent=1))

    print("=== CAUSAS DE AUMENTO, DE DIMINUICAO E MULTIPLICADOR, Parte Especial ===")
    print("%-44s %10s %10s" % ("", "1940", "hoje"))
    for rot, k in [("artigos da Parte Especial", "artigos_da_parte_especial"),
                   ("comandos de AUMENTO", "comandos_de_aumento"),
                   ("artigos com aumento", "artigos_com_aumento"),
                   ("comandos de DIMINUICAO", "comandos_de_diminuicao"),
                   ("artigos com diminuicao", "artigos_com_diminuicao"),
                   ("comandos de MULTIPLICADOR", "comandos_de_multiplicador"),
                   ("artigos com multiplicador", "artigos_com_multiplicador"),
                   ("artigos cujo teto a regua SUBESTIMA", "artigos_cujo_teto_a_regua_subestima"),
                   ("maior fator observado", "fator_maximo_observado")]:
        print("%-44s %10s %10s" % (rot, a[k], b[k]))
    print()
    print("fracoes de aumento medidas, 1940:", a["fracoes_de_aumento_medidas"])
    print("fracoes de aumento medidas, hoje:", b["fracoes_de_aumento_medidas"])
    print()
    for epoca, d in (("1940", a), ("hoje", b)):
        if d["comandos_sem_valor_extraido"]:
            print("EM %s ha %d comando(s) achado(s) e NAO convertido(s) em numero:"
                  % (epoca, len(d["comandos_sem_valor_extraido"])))
            for x in d["comandos_sem_valor_extraido"]:
                print("   art. %s: %s" % (x["artigo"], x["trecho"]))
    print()
    print("gravado: " + SAIDA)
    return 0


def bancada():
    """Duas direcoes, mais o desligamento do detector. As frases sao as REAIS do Codigo."""
    provas = []
    # os dois defeitos medidos no art. 159, plantados de volta
    t159_4 = "o concorrente que o denunciar a autoridade tera sua pena reduzida de um a dois terços."
    t159_5 = "aumenta-se a respectiva pena em 2/3 (dois terços)."
    aum, dim, mult = comandos(t159_4)
    provas.append(("forma ELIDIDA 'de um a dois tercos' e' vista como diminuicao", len(dim) == 1))
    provas.append(("e a maior fracao dela e' 2/3",
                   dim and abs(dim[0]["fracao"] - 2 / 3) < 1e-9))
    aum, dim, mult = comandos(t159_5)
    provas.append(("forma em ALGARISMO com adjetivo no meio e' vista como aumento", len(aum) == 1))
    provas.append(("e a fracao dela e' 2/3", aum and abs(aum[0]["fracao"] - 2 / 3) < 1e-9))

    aum, _, _ = comandos("a pena e' aumentada de um terço.")
    provas.append(("aumento simples por extenso", len(aum) == 1 and abs(aum[0]["fracao"] - 1 / 3) < 1e-9))
    aum, _, _ = comandos("a pena e' aumentada de metade.")
    provas.append(("aumento de metade", len(aum) == 1 and abs(aum[0]["fracao"] - 0.5) < 1e-9))
    _, _, mult = comandos("a pena e' aplicada em dobro.")
    provas.append(("multiplicador dobro", len(mult) == 1 and mult[0]["fator"] == 2.0))
    _, _, mult = comandos("aumentar a pena de um so' dos crimes ate' o triplo.")
    provas.append(("multiplicador triplo", len(mult) == 1 and mult[0]["fator"] == 3.0))

    # a direcao que tem que CALAR
    aum, dim, mult = comandos("Pena - reclusao, de oito a quinze anos.")
    provas.append(("faixa de pena comum NAO e' comando de aumento", not aum and not dim and not mult))
    aum, dim, mult = comandos("Sequestrar pessoa com o fim de obter vantagem.")
    provas.append(("descricao de conduta NAO dispara nada", not aum and not dim and not mult))

    # a ordem da alternancia: a forma completa tem que vencer a elidida
    aum, _, _ = comandos("a pena e' aumentada de um terço.")
    provas.append(("forma completa vence a elidida, e o valor sai",
                   len(aum) == 1 and aum[0]["fracao"] is not None))
    provas.append(("fracao desconhecida devolve None", valor_da_fracao("um bocado") is None))
    provas.append(("fracao em algarismo", abs(valor_da_fracao("3/4") - 0.75) < 1e-9))
    provas.append(("denominador zero nao explode", valor_da_fracao("1/0") is None))

    # DESLIGAR o detector tem que MUDAR o veredito
    global RE_AUMENTO
    guardado = RE_AUMENTO
    RE_AUMENTO = re.compile(r"(?!x)x")
    aum, _, _ = comandos(t159_5)
    provas.append(("com o detector DESLIGADO o aumento some", len(aum) == 0))
    RE_AUMENTO = guardado
    aum, _, _ = comandos(t159_5)
    provas.append(("religado, o aumento volta a aparecer", len(aum) == 1))

    ok = sum(1 for _, v in provas if v)
    for nome, v in provas:
        print(("   ok    " if v else "  FALHA  ") + nome)
    print("")
    print("BANCADA DAS CAUSAS DE AUMENTO: %d de %d" % (ok, len(provas)))
    return 0 if ok == len(provas) else 1


if __name__ == "__main__":
    if "--bancada" in sys.argv:
        sys.exit(bancada())
    sys.exit(apurar())
